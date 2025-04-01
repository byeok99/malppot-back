import httpx
from malppot.conf.settings import HeyGenConfig
from sqlalchemy import text

class HeyGenService:
    def __init__(self, config: HeyGenConfig, db):
        if isinstance(config, dict):
            config = HeyGenConfig(**config)
        self.config = config
        self.db = db

    async def generate_video(self, script: str, user_idx:int) -> str:
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
                  "locale": "ko-KR"
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