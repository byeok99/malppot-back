# service.py
import httpx
import aiofiles
import os
import asyncio
from uuid import uuid4
from pathlib import Path

class HeyGenService:
    def __init__(self, api_key: str, base_url: str, avatar_id: str, voice_id: str):
        self.api_key = api_key
        self.base_url = base_url
        self.fixed_avatar_id = avatar_id
        self.fixed_voice_id = voice_id

    async def generate_video(self, script: str) -> str:
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": self.api_key
        }

        payload = {
            "script": script,
            "avatar_id": self.fixed_avatar_id,
            "voice_id": self.fixed_voice_id,
            "caption": False,
            "dimension": {"width": 1280, "height": 720}
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/video/generate", json=payload, headers=headers)
            response.raise_for_status()
            task_id = response.json()["task_id"]

            for _ in range(60):
                await asyncio.sleep(2)
                status_resp = await client.get(f"{self.base_url}/video/status", params={"task_id": task_id}, headers=headers)
                status_data = status_resp.json()
                if status_data.get("status") == "done":
                    return status_data["video_url"]
                elif status_data.get("status") == "failed":
                    raise Exception("Video generation failed.")

            raise TimeoutError("Video generation took too long.")

    async def download_and_store_video(self, video_url: str, save_directory: str = "static/generated_videos") -> Path:
        os.makedirs(save_directory, exist_ok=True)
        filename = f"video_{uuid4().hex}.mp4"
        save_path = Path(save_directory) / filename

        async with httpx.AsyncClient() as client:
            response = await client.get(video_url)
            response.raise_for_status()
            async with aiofiles.open(save_path, "wb") as f:
                await f.write(response.content)

        return save_path