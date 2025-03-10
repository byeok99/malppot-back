import json
import asyncio
import websockets
from contextlib import asynccontextmanager
from typing import AsyncGenerator, AsyncIterator, Any, Callable, Coroutine
from langchain_core._api import beta
from pydantic import BaseModel, Field

# DEFAULT_URL = "wss://api.openai.com/v1/realtime"

EVENTS_TO_IGNORE = {
    "response.function_call_arguments.delta",
    "rate_limits.updated",
    "response.audio_transcript.delta",
    "response.created",
    "response.content_part.added",
    "response.content_part.done",
    "conversation.item.created",
    "response.audio.done",
    "session.created",
    "session.updated",
    "response.done",
    "response.output_item.done",
}

@asynccontextmanager
async def connect(*, api_key: str, model: str, url: str) -> AsyncGenerator[
    tuple[
        Callable[[dict[str, Any] | str], Coroutine[Any, Any, None]],
        AsyncIterator[dict[str, Any]],
    ],
    None,
]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "OpenAI-Beta": "realtime=v1",
    }
    url += f"?model={model}"
    websocket = await websockets.connect(url, extra_headers=headers)

    try:
        async def send_event(event: dict[str, Any] | str) -> None:
            formatted_event = json.dumps(event) if isinstance(event, dict) else event
            await websocket.send(formatted_event)

        async def event_stream() -> AsyncIterator[dict[str, Any]]:
            async for raw_event in websocket:
                yield json.loads(raw_event)

        stream: AsyncIterator[dict[str, Any]] = event_stream()

        yield send_event, stream
    finally:
        await websocket.close()

async def amerge(**streams: AsyncIterator[Any]) -> AsyncIterator[tuple[str, Any]]:
    """Merge multiple streams into one stream."""
    nexts: dict[asyncio.Task, str] = {
        asyncio.create_task(anext(stream)): key for key, stream in streams.items()
    }
    while nexts:
        done, _ = await asyncio.wait(nexts, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            key = nexts.pop(task)
            stream = streams[key]
            try:
                yield key, task.result()
                nexts[asyncio.create_task(anext(stream))] = key
            except StopAsyncIteration:
                pass
            except Exception as e:
                for task in nexts:
                    task.cancel()
                raise e

@beta()
class OpenAIVoiceReactAgent(BaseModel):
    model: str
    api_key: str
    instructions: str
    url: str

    async def aconnect(
        self,
        input_stream: AsyncIterator[str],
        send_output_chunk: Callable[[str], Coroutine[Any, Any, None]],
    ) -> None: # str
        """
        Connect to the OpenAI API and send and receive messages.

        input_stream: AsyncIterator[str]
            Stream of input events to send to the model. Usually transports input_audio_buffer.append events from the microphone.
        output: Callable[[str], None]
            Callback to receive output events from the model. Usually sends response.audio.delta events to the speaker.

        """
        # formatted_tools: list[BaseTool] = [
        #     tool if isinstance(tool, BaseTool) else tool_converter.wr(tool)  # type: ignore
        #     for tool in self.tools or []
        # ]
        # tools_by_name = {tool.name: tool for tool in self.tools}
        # tool_executor = VoiceToolExecutor(tools_by_name=tools_by_name)

        async with connect(
            model=self.model, api_key=self.api_key, url=self.url
        ) as (
            model_send,
            model_receive_stream,
        ):
            # sent tools and instructions with initial chunk
            # tool_defs = [
            #     {
            #         "type": "function",
            #         "name": tool.name,
            #         "description": tool.description,
            #         "parameters": {"type": "object", "properties": tool.args},
            #     }
                # for tool in tools_by_name.values()
            # ]
            await model_send(
                {
                    "type": "session.update",
                    "session": {
                        "instructions": self.instructions,
                        "input_audio_transcription": {
                            "model": "whisper-1",
                        },
                        # "tools": tool_defs,
                    },
                }
            )
            async for stream_key, data_raw in amerge(
                input_mic=input_stream,
                output_speaker=model_receive_stream,
                # tool_outputs=tool_executor.output_iterator(),
            ):
                try:
                    data = (
                        json.loads(data_raw) if isinstance(data_raw, str) else data_raw
                    )
                except json.JSONDecodeError:
                    print("error decoding data:", data_raw)
                    continue

                if stream_key == "input_mic":
                    await model_send(data)
                # elif stream_key == "tool_outputs":
                #     print("tool output", data)
                #     await model_send(data)
                #     await model_send({"type": "response.create", "response": {}})
                elif stream_key == "output_speaker":
                    t = data["type"]
                    if t == "response.audio.delta":
                        await send_output_chunk(json.dumps(data))
                    elif t == "response.audio_buffer.speech_started":
                        print("interrupt")
                        send_output_chunk(json.dumps(data))
                    elif t == "error":
                        print("error:", data)
                    # elif t == "response.function_call_arguments.done":
                    #     print("tool call", data)
                        # await tool_executor.add_tool_call(data)
                    elif t == "conversation.item.input_audio_transcription.completed":
                        print("user:", data["transcript"])
                        yield {"user": data["transcript"]}
                    elif t == "response.audio_transcript.done":
                        print("model:", data["transcript"])
                        yield {"model": data["transcript"]}
                    elif t in EVENTS_TO_IGNORE:
                        pass
                    else:
                        print(t)


__all__ = ["OpenAIVoiceReactAgent"]
