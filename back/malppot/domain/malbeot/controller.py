import logging

from fastapi import APIRouter, WebSocket, Depends, status, Query

from malppot.common.dependencies import get_current_user_ws
from malppot.common.di_providers import (
    get_malbeot_service_from_di
)

logger = logging.getLogger(__name__)

router = APIRouter()


async def _close_websocket_with_error(websocket: WebSocket, reason: str, code: int = status.WS_1008_POLICY_VIOLATION):
    logger.warning(f"Closing WebSocket connection: {reason}")
    await websocket.send_json({
        "type": "error",
        "message": reason
    })
    await websocket.close(code=code, reason=reason)


@router.websocket("/ws")
async def chat_with_malbeot(
        websocket: WebSocket,
        malbeot_service=Depends(get_malbeot_service_from_di),
        mode: str = Query(...),
):
    await websocket.accept()

    try:
        user = get_current_user_ws(websocket)
        await malbeot_service.serve(websocket, mode, user.user_idx)

    except Exception as e:
        await _close_websocket_with_error(websocket, str(e), code=status.WS_1011_INTERNAL_ERROR)
