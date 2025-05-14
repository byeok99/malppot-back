from fastapi import APIRouter, Request, HTTPException
from dependency_injector.wiring import inject, Provide
from malppot.domain.heygen.schema import HeyGenGenerateRequest, HeyGenVideoResponse
from malppot.di import DI

router = APIRouter()

@router.post("/generate-video", response_model=HeyGenVideoResponse)
@inject
async def generate_video(
    request: Request,
    body: HeyGenGenerateRequest,
    heygen_service = Provide[DI.heygen.service],
    jwt_service = Provide[DI.jwt_service],
    auth_service = Provide[DI.auth.service],
):
    auth_header = request.headers.get("Authorization")
    token = auth_header.replace("Bearer ", "").strip() if auth_header else None
    user_id = jwt_service.get_user_id(token)
    user = auth_service.get_user_by_id(user_id)

    video_id = await heygen_service.generate_video(script=body.text, user_idx=user.user_idx)
    print(video_id)
    return {"video_id": video_id}

@router.post("/callback")
@inject
async def heygen_callback(
    request: Request,
    heygen_service = Provide[DI.heygen.service],
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
    #video_url = raw_url.split("?")[0] if raw_url else None

    if not video_id or not video_url:
        return {"message": "Missing video_id or url"}

    heygen_service.update_video(video_id=video_id, video_url=video_url)

@router.get("/videos/{video_id}")
@inject
async def get_video_by_id(
    video_id: str,
    request: Request,
    jwt_service = Provide[DI.jwt_service],
    auth_service = Provide[DI.auth.service],
    heygen_service = Provide[DI.heygen.service],
):
    auth_header = request.headers.get("Authorization")
    token = auth_header.replace("Bearer ", "").strip() if auth_header else None
    user_id = jwt_service.get_user_id(token)
    user = auth_service.get_user_by_id(user_id)

    return heygen_service.get_video(video_id=video_id, user_idx=user.user_idx)