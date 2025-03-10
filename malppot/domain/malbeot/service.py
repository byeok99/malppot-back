from fastapi import WebSocket
from malppot.conf.settings import OpenAIConfig
from typing import AsyncIterator, Any
from malppot.domain.malbeot.agent import OpenAIVoiceReactAgent

class MalbeotService:
    def __init__(self, config: OpenAIConfig, db):
        if isinstance(config, dict):
            config = OpenAIConfig(**config)
        self.config = config
        self.db = db

    async def serve(self, websocket: WebSocket):
        await websocket.accept()
        print(f"Client connected: {websocket.client}")
        browser_receive_stream = self.websocket_stream(websocket)
        agent = OpenAIVoiceReactAgent(
            model=self.config.model,
            api_key=self.config.api_key,
            instructions=self.config.instruction,
        )

        await agent.aconnect(browser_receive_stream, websocket.send_text)
        print(f"Client disconnected: {websocket.client}")

    async def websocket_stream(self, websocket: WebSocket) -> AsyncIterator[str]:
        """WebSocket을 통해 클라이언트로부터 메시지를 받음"""
        while True:
            try:
                data = await websocket.receive_text()
                yield data
            except Exception:
                break