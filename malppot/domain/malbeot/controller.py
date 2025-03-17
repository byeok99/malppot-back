from fastapi import APIRouter, WebSocket, HTTPException
from fastapi.responses import HTMLResponse
from typing import List
from malppot.domain.malbeot.schema import ChatRequest, ChatResponse
from dependency_injector.wiring import Provide, inject
from malppot.di import DI
from pathlib import Path
import jwt

router = APIRouter()

@router.websocket("/ws")
@inject
async def websocket_endpoint(
        websocket: WebSocket,
        malbeot_service = Provide(DI.malbeot.service),
        jwt_service = Provide(DI.jwt_service),
        auth_service = Provide(DI.auth.service),
):
    token = websocket.query_params.get("access_token")
    if not token:
        print("No access token")
        await websocket.close(code=1008)
        return
    try:
        user_id = jwt_service.get_user_id(token)
        if not user_id:
            print("Invalid Token")
            await websocket.close(code=1008)  # Invalid Token
            return
    except jwt.ExpiredSignatureError:
        print("Token has expired")
        await websocket.close(code=1008)
        return

    try:
        user = auth_service.get_user_by_id(user_id)
    except HTTPException as e:
        print(f"User not found: {e.detail}")
        await websocket.close(code=1008)
        return

    await malbeot_service.serve(websocket, user.user_idx)

@router.get("/")
async def homepage():
    INDEX_HTML_PATH = Path(__file__).resolve().parent.parent.parent / "static" / "index.html"
    with open(INDEX_HTML_PATH) as f:
        html = f.read()
    return HTMLResponse(html)

@router.post("/chats",  response_model=List[ChatResponse])
@inject
async def chats(
        input: ChatRequest,
        malbeot_service = Provide(DI.malbeot.service),
):
    return await malbeot_service.get_chat_list(input.user_idx)