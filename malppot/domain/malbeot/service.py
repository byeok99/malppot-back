from fastapi import WebSocket
from malppot.conf.settings import OpenAIConfig
from typing import AsyncIterator
from malppot.domain.malbeot.agent import OpenAIVoiceReactAgent

class MalbeotService:
    def __init__(self, config: OpenAIConfig, db):
        if isinstance(config, dict):
            config = OpenAIConfig(**config)
        self.config = config
        self.db = db

    async def serve(self, websocket: WebSocket, user_idx: int):
        await websocket.accept()

        browser_receive_stream = self.websocket_stream(websocket)
        agent = OpenAIVoiceReactAgent(
            model=self.config.model,
            api_key=self.config.api_key,
            url=self.config.url,
            instructions=self.config.instruction,
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
