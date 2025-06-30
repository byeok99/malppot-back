from dependency_injector.wiring import inject
from fastapi import APIRouter, Request, Depends

from malppot.common.di_providers import get_heygen_service_from_di
from malppot.domain.heygen.schema import HeyGenGenerateRequest, HeyGenVideoResponse
from malppot.domain.heygen.service import HeyGenService

router = APIRouter()


@router.get("/test")
async def test(
        heygen_service: HeyGenService = Depends(get_heygen_service_from_di)
):
    await heygen_service.generate_video("집에")


@router.post("/generate-video", response_model=HeyGenVideoResponse)
async def generate_video(
        body: HeyGenGenerateRequest,
        heygen_service: HeyGenService = Depends(get_heygen_service_from_di),

):
    video_id = await heygen_service.generate_video(script=body.text)
    return {"video_id": video_id}


@router.post("/callback")
@inject
async def heygen_callback(
        request: Request,
        heygen_service=Depends(get_heygen_service_from_di),
):
    data = await request.json()
    print("콜백 수신:", data)

    event_type = data.get("event_type")
    if event_type != "avatar_video.success":
        print(f"무시된 이벤트: {event_type}")
        return {"message": "Skipped non-video callback"}

    event_data = data.get("event_data", {})
    video_id = event_data.get("video_id")
    video_url = event_data.get("url")

    if not video_id or not video_url:
        return {"message": "Missing video_id or url"}

    heygen_service.update_video(video_id=video_id, video_url=video_url)


@router.get("/videos/{script}")
@inject
async def get_video(
        script: str,
        heygen_service=Depends(get_heygen_service_from_di),
):
    return await heygen_service.get_video(script=script)
