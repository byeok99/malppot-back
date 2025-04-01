from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from dependency_injector.wiring import inject, Provide
from sqlalchemy import text
from malppot.di import DI

router = APIRouter()

class HeyGenGenerateRequest(BaseModel):
    text: str

class HeyGenVideoResponse(BaseModel):
    video_url: str

@router.post("/generate-video", response_model=HeyGenVideoResponse)
@inject
async def generate_video(
    request: Request,  # <-- 쿼리 파라미터를 받기 위해 추가
    body: HeyGenGenerateRequest,  # 본문에서 받는 실제 텍스트
    heygen_service = Provide[DI.heygen.service],
    jwt_service = Provide[DI.jwt_service],
    auth_service = Provide[DI.auth.service],
):
    token = request.query_params.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Access token missing")

    user_id = jwt_service.get_user_id(token)
    user = auth_service.get_user_by_id(user_id)

    # user.user_idx 같은 걸 활용해서 내부에서 DB에 기록하는 것도 가능
    video_id = await heygen_service.generate_video(script=body.text, user_id=user.user_idx)

    return {"video_id": video_id}

@router.post("/heygen/callback")
@inject
async def heygen_callback(
    request: Request,
    db = Provide[DI.db]
):
    data = await request.json()
    print("📩 콜백 수신:", data)

    video_id = data.get("video_id")
    video_url = data.get("video_url")

    if not video_id:
        return {"message": "Missing video_id"}

    session = db.get_session()
    try:
        session.execute(
            text("""
                UPDATE video_logs
                SET
                    video_url = :video_url
                WHERE video_id = :video_id
            """),
            {
                "video_id": video_id,
                "video_url": video_url,
            }
        )
        session.commit()
        return {"message": "Callback handled successfully"}
    except Exception as e:
        session.rollback()
        print(f"❌ DB 업데이트 실패: {e}")
        return {"message": "Internal server error"}
    finally:
        session.close()
        
@router.get("/videos/{video_id}")
@inject
async def get_video_by_id(
    video_id: str,
    request: Request,
    jwt_service = Provide[DI.jwt_service],
    auth_service = Provide[DI.auth.service],
    db = Provide[DI.db],
):
    token = request.query_params.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Access token missing")

    user_id = jwt_service.get_user_id(token)
    user = auth_service.get_user_by_id(user_id)

    session = db.get_session()
    try:
        result = session.execute(
            text("""
                SELECT video_id, script, status, video_url, created_at
                FROM video_logs
                WHERE video_id = :video_id AND user_id = :user_id
            """),
            {"video_id": video_id, "user_id": user.user_idx}
        )
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="해당 영상이 없거나 권한이 없습니다.")
        return dict(row)
    finally:
        session.close()