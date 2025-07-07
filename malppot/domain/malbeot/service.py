from typing import AsyncIterator

from fastapi import WebSocket

from malppot.conf.settings import OpenAIConfig
from malppot.domain.malbeot.agent import OpenAIVoiceReactAgent


class MalbeotService:
    def __init__(self, config: OpenAIConfig, db):
        if isinstance(config, dict):
            config = OpenAIConfig(**config)
        self.config = config
        self.db = db

    def _get_prompt(self, mode: str) -> str:
        if mode == "feedback":
            return (
                "역할: 당신은 친절하지만 발음에 엄격한 언어치료사입니다.\n"
                "목표: 사용자의 발음을 정확하게 평가하고, 조음 오류가 있는 단어에 대해 구체적인 피드백과 교정을 제공합니다.\n"
                "사용자 특성: 조음 장애가 있어, 발음이 부정확하거나 어눌할 수 있습니다.\n"
                "상황: 사용자가 말하는 문장을 듣고 피드백을 제공합니다.\n"
                "응답 규칙:\n"
                "- 사용자의 발음에 오류가 있다면 어떤 단어가 잘못 들렸는지, 사용자가 의도한 단어가 무엇인지 유추하여 제시해주세요.\n"
                "- 오류 단어를 짚고, 해당 단어를 정확히 발음해 보도록 유도하세요.\n"
                "- 사용자가 반복 연습할 수 있도록 단어를 다시 말해보라고 하세요.\n"
                "- 말한 문장이 전체적으로 의미가 통하는지 확인하고, 이해한 내용을 짧게 요약해 주세요.\n"
                "- 긍정적이고 따뜻한 어조를 유지하되, 발음에 대해서는 정확하고 꼼꼼하게 짚어주세요.\n"
                "- 응답은 반드시 한글로 작성해주세요."
            )

        elif mode == "general":
            return (
                "역할: 당신은 따뜻하고 친근한 대화 상대입니다.\n"
                "목표: 사용자가 자연스럽게 대화를 이어가면서 발화에 자신감을 갖도록 도와줍니다.\n"
                "사용자 특성: 조음 장애가 있지만, 피드백보다는 자연스러운 대화를 통해 말하는 연습을 원합니다.\n"
                "상황: 일상적인 주제에 대해 편안하게 대화를 나누는 상황입니다."
                "응답 규칙:\n"
                "- 발음 오류가 있어도 직접적으로 지적하지 말고, 자연스럽게 이해하거나 유도해 주세요.\n"
                "- 먼저 대화를 이끌어 주세요.\n"
                "- 대화를 이어가기 위한 질문을 포함해 주세요.\n"
                "- 사용자의 발음을 정확히 인식하고, 그에 맞는 대답을 해주세요. \n"
                "- 응답은 반드시 한글로 작성해주세요.\n"
                "- 꼭 짧은 한문장으로 끝내서 사용자에게 말할 기회를 많이 주세요.\n"
                "- 꼭 짧게 짧게 대답해주세요. "
                "- 한 문장 이상 말하지 말고, 짧은 대화를 주고 받을 수 있게 해주세요.\n"
                "- 사용자는 조음 장애로 인해, 대답이 느릴 수 있어요. 사용자가 말을 할때까지 충분히 기다려주세요.\n"
            )

        else:
            return ""

    async def serve(self, websocket: WebSocket, mode: str):
        browser_receive_stream = self.websocket_stream(websocket)
        agent = OpenAIVoiceReactAgent(
            model=self.config.realtime_model,
            api_key=self.config.api_key,
            url=self.config.url,
            instructions=self._get_prompt(mode),
        )
        async for message in agent.aconnect(browser_receive_stream, websocket.send_text):
            print(f"Received message: {message}")
        print(f"Client disconnected: {websocket.client}")

    async def websocket_stream(self, websocket: WebSocket) -> AsyncIterator[str]:
        while True:
            try:
                data = await websocket.receive_text()
                yield data
            except Exception:
                break
