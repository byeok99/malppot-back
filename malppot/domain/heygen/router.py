from fastapi import APIRouter, Depends
from pydantic import BaseModel
from malppot.domain.heygen.service import HeyGenService
from dependency_injector.wiring import inject, Provide
from malppot.di import DI
from pathlib import Path

router = APIRouter(prefix="/heygen", tags=["heygen"])

class HeyGenGenerateRequest(BaseModel):
    text: str

class HeyGenVideoResponse(BaseModel):
    video_url: str

@router.post("/generate-video", response_model=HeyGenVideoResponse)
@inject
async def generate_video(
    request: HeyGenGenerateRequest,
    heygen_service: HeyGenService = Depends(Provide[DI.heygen_service])
):
    video_url = await heygen_service.generate_video(script=request.text)
    local_path = await heygen_service.download_and_store_video(video_url)
    relative_url = f"/static/generated_videos/{Path(local_path).name}"
    return {"video_url": relative_url}