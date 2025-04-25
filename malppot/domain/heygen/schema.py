# schema.py
from pydantic import BaseModel

class HeyGenGenerateRequest(BaseModel):
    text: str

class HeyGenVideoResponse(BaseModel):
    video_id: str