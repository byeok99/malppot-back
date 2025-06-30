from datetime import datetime, timedelta

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from malppot.conf.settings import HeyGenConfig
from malppot.domain.models import VideoLog, VideoLogStatus


class HeyGenService:
    def __init__(self, config: HeyGenConfig, db):
        if isinstance(config, dict):
            config = HeyGenConfig(**config)
        self.config = config
        self.db = db

    def update_video(self, video_id: str, video_url: str):
        session = self.db.get_session()
        try:
            video_log = session.query(VideoLog).filter(VideoLog.video_id == video_id).first()
            if not video_log:
                raise HTTPException(status_code=404, detail="업데이트할 영상을 찾을 수 없습니다.")

            video_log.video_url = video_url
            video_log.status = VideoLogStatus.DONE
            session.commit()
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=f"DB update error: {e}")
        finally:
            session.close()

    async def generate_video(self, script: str):
        session: Session = self.db.get_session()
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        try:
            existing_video = session.query(VideoLog).filter(
                VideoLog.script == script,
                VideoLog.created_at >= one_week_ago,
            ).order_by(VideoLog.created_at.desc()).first()

            if existing_video:
                return
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
                        "emotion": 'Friendly',
                        "speed": 0.7,
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
            response = await client.post(
                f"{self.config.base_url}/video/generate",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            response_data = response.json()
            video_id = response_data["data"]["video_id"]

            session = self.db.get_session()
            try:
                new_video_log = VideoLog(
                    video_id=video_id,
                    script=script,
                    status=VideoLogStatus.PENDING,
                )
                session.add(new_video_log)
                session.commit()
            finally:
                session.close()

    async def get_video(self, script: str):
        session: Session = self.db.get_session()
        one_week_ago = datetime.utcnow() - timedelta(days=7)  # 일주일 전 시간 계산
        try:
            video_log = session.query(VideoLog).filter(
                VideoLog.script == script,
                VideoLog.status == VideoLogStatus.DONE,
                VideoLog.created_at >= one_week_ago
            ).order_by(VideoLog.created_at.desc()).first()

            if video_log:
                return video_log.video_url
            return None
        finally:
            session.close()
