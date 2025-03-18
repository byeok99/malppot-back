from pydantic import BaseModel
from datetime import datetime

class ChatRequest(BaseModel):
    user_idx: int

class ChatResponse(BaseModel):
    log_idx: int
    user_idx: int
    session_id: int
    chat_text: str
    speaker: str
    created_date: datetime

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
        }

__all__ = (
    "ChatRequest",
    "ChatResponse",
)