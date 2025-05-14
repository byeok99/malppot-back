import httpx
from malppot.conf.settings import HeyGenConfig
from fastapi import HTTPException
from sqlalchemy import text
from datetime import datetime, timedelta

class HeyGenService:
    def __init__(self, config: HeyGenConfig, db):
        if isinstance(config, dict):
            config = HeyGenConfig(**config)
        self.config = config
        self.db = db
    def get_video(self, video_id: str, user_idx:int):
        session = self.db.get_session()
        try:
            result = session.execute(
                text("""
                    SELECT video_id, script, status, video_url, created_at
                    FROM video_logs
                    WHERE video_id = :video_id
                """),
                {"video_id": video_id}
            )
            row = result.mappings().fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="해당 영상이 없거나 권한이 없습니다.")
            return dict(row)
        finally:
            session.close()  
    
    def update_video(self, video_id: str, video_url: str):
        session = self.db.get_session()
        try:
            session.execute(
                text("""
                    UPDATE video_logs
                    SET video_url = :video_url,
                        status = :status
                    WHERE video_id = :video_id
                """),
                {
                    "video_id": video_id,
                    "video_url": video_url,
                    "status": "done"
                }
            )
            session.commit()
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=f"DB update error: {e}")
        finally:
            session.close()
        
    async def generate_video(self, script: str, user_idx:int) -> str:
        try:
            one_week_ago = datetime.utcnow() - timedelta(days=7)

            # 1. 최근 7일 이내 동일 스크립트 조회
            result = session.execute(
                text("""
                SELECT video_id
                FROM video_logs
                WHERE script = :script
                  AND user_id = :user_id
                  AND created_at >= :threshold
                  AND status = 'done'
                ORDER BY created_at DESC
                LIMIT 1
                """),
                {
                    "script": script,
                    "user_id": user_idx,
                    "threshold": one_week_ago,
                }
            )
            row = result.fetchone()
            if row:
                print(f"중복 스크립트 : video_id = {row.video_id}")
                return row.video_id
        finally:
            session.close()

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": self.config.api_key
        }

        payload = {
            "caption": False,
            "dimension": {
              "width": 1280,
              "height": 720
            },
            "video_inputs": [
              {
                "character": {
                  "type": "avatar",
                  "avatar_id": self.config.avatar_id
                },
                "voice": {
                  "type": "text",
                  "voice_id": self.config.voice_id,
                  "input_text": script,
                  "emotion" : 'Friendly',
                  "locale": 'ko-KR'
                },
                "background": {
                  "type": "color",
                  "value": "#ffffff"
                }
              }
            ],
            "callback_url": self.config.callback_url
        }
        async with httpx.AsyncClient() as client:
                    # 1. 영상 생성 요청
                    response = await client.post(
                        f"{self.config.base_url}/video/generate",
                        json=payload,
                        headers=headers
                    )
                    response.raise_for_status()
                    response_data = response.json()
                    video_id = response_data["data"]["video_id"]
                    print("📦 생성된 video_id:", video_id)

                    session = self.db.get_session()
                    try:
                        session.execute(
                            text("""
                            INSERT INTO video_logs (video_id, user_id, script, status)
                            VALUES (:video_id, :user_id, :script, :status)
                            """),
                            {
                                "video_id": video_id,
                                "user_id": user_idx,
                                "script": script,
                                "status": "pending",
                            }
                        )
                        session.commit()
                    finally:
                        session.close()

                    return video_id
