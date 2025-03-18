import uuid
from typing import List
from fastapi import WebSocket
from malppot.conf.settings import OpenAIConfig
from typing import AsyncIterator
from malppot.domain.malbeot.agent import OpenAIVoiceReactAgent
from malppot.domain.malbeot.model import AIMalbeotLog
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from malppot.domain.malbeot.schema import ChatResponse

class MalbeotService:
    def __init__(self, config: OpenAIConfig, db):
        if isinstance(config, dict):
            config = OpenAIConfig(**config)
        self.config = config
        self.db = db

    async def serve(self, websocket: WebSocket, user_idx: int):
        await websocket.accept()
        session_id = uuid.uuid4().int >> 64

        browser_receive_stream = self.websocket_stream(websocket)
        agent = OpenAIVoiceReactAgent(
            model=self.config.model,
            api_key=self.config.api_key,
            url=self.config.url,
            instructions=self.config.instruction,
        )

        async for message in agent.aconnect(browser_receive_stream, websocket.send_text):
            print(f"Received message: {message}")
            await self.save_log(user_idx, session_id, message)
        print(f"Client disconnected: {websocket.client}")

    async def websocket_stream(self, websocket: WebSocket) -> AsyncIterator[str]:
        while True:
            try:
                data = await websocket.receive_text()
                yield data
            except Exception:
                break

    async def save_log(self, user_idx:int, session_id: int, message: dict[str, str]):
        session = self.db.get_session()
        try:
            for speaker, text in message.items():
                log = AIMalbeotLog(
                    user_idx=user_idx,
                    session_id=session_id,
                    speaker=speaker,
                    chat_text=text,
                )

                session.add(log)
                session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error saving log: {e}")

    async def get_chat_list(self, user_idx: int) -> List[ChatResponse]:
        session: AsyncSession = self.db.get_session()

        row_number_column = func.row_number().over(
            partition_by=AIMalbeotLog.session_id,
            order_by=AIMalbeotLog.log_idx.asc()
        ).label("rn")

        ranked_logs_cte = (
            select(
                AIMalbeotLog,
                row_number_column
            )
            .where(AIMalbeotLog.user_idx == user_idx)
            .cte("ranked_logs")
        )

        query = (
            select(
                ranked_logs_cte.c.log_idx,
                ranked_logs_cte.c.user_idx,
                ranked_logs_cte.c.session_id,
                ranked_logs_cte.c.chat_text,
                ranked_logs_cte.c.speaker,
                ranked_logs_cte.c.created_date,
            )
            .where(ranked_logs_cte.c.rn == 1)
            .order_by(desc(ranked_logs_cte.c.created_date))
        )
        return session.execute(query).all()

    async def get_chat(self, session_id: int) -> List[ChatResponse]:
        session: AsyncSession = self.db.get_session()

        query = (
            select(
                AIMalbeotLog.log_idx,
                AIMalbeotLog.user_idx,
                AIMalbeotLog.session_id,
                AIMalbeotLog.chat_text,
                AIMalbeotLog.speaker,
                AIMalbeotLog.created_date,
            )
            .where(AIMalbeotLog.session_id == session_id)
            .order_by(AIMalbeotLog.log_idx.asc())
        )

        return session.execute(query).all()
