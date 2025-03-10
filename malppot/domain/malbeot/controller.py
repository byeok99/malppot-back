from fastapi import APIRouter, WebSocket, Depends
from fastapi.responses import HTMLResponse

from malppot.domain.malbeot.service import MalbeotService
from malppot.di import DI
from pathlib import Path


router = APIRouter()

def get_malbeot_service() -> MalbeotService:
    return DI.malbeot.service()

@router.websocket("/ws")
async def websocket_endpoint(
        websocket: WebSocket,
        service: MalbeotService = Depends(get_malbeot_service),
):
    await service.serve(websocket)


@router.get("/")
async def homepage():
    INDEX_HTML_PATH = Path(__file__).resolve().parent.parent.parent / "static" / "index.html"
    with open(INDEX_HTML_PATH) as f:
        html = f.read()
    return HTMLResponse(html)
