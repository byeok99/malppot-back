import logging

import jwt
from fastapi import APIRouter, WebSocket, HTTPException, Depends, status, Query

from malppot.common.di_providers import (
    get_malbeot_service_from_di,
    get_jwt_service_from_di,
    get_auth_service_from_di
)
from malppot.common.errors import UserNotFoundException
from malppot.domain.models import User

logger = logging.getLogger(__name__)

router = APIRouter()


async def _close_websocket_with_error(websocket: WebSocket, reason: str, code: int = status.WS_1008_POLICY_VIOLATION):
    logger.warning(f"Closing WebSocket connection: {reason}")
    await websocket.close(code=code, reason=reason)


@router.websocket("/ws")
async def chat_with_malbeot(
        websocket: WebSocket,
        malbeot_service=Depends(get_malbeot_service_from_di),
        auth_service=Depends(get_auth_service_from_di),
        jwt_service=Depends(get_jwt_service_from_di),
        access_token: str = Query(...),
        mode: str = Query(...),
):
    await websocket.accept()
    
    if not access_token:
        await _close_websocket_with_error(websocket, "No access token provided.")
        return

    user_id = None
    try:
        user_id = jwt_service.get_user_id(access_token)
        if not user_id:
            await _close_websocket_with_error(websocket, "Invalid Token.")
            return
    except jwt.ExpiredSignatureError:
        await _close_websocket_with_error(websocket, "Token has expired.")
        return
    except Exception as e:
        logger.exception(f"Error parsing JWT token: {e}")
        await _close_websocket_with_error(websocket, "Token processing error.")
        return

    try:
        user: User = auth_service.get_user_by_id(user_id)
        if user is None:
            await _close_websocket_with_error(websocket, "User not found.")
            return
    except UserNotFoundException as e:
        logger.error(f"User not found via AuthService: {e.detail}")
        await _close_websocket_with_error(websocket, f"User lookup failed: {e.detail}")
        return
    except HTTPException as e:
        logger.error(f"User lookup failed (HTTPException): {e.detail}")
        await _close_websocket_with_error(websocket, f"User lookup failed: {e.detail}")
        return
    except Exception as e:
        logger.exception(f"Unexpected error during user lookup for WebSocket: {e}")
        await _close_websocket_with_error(websocket, "Internal server error during user lookup.")
        return

    await malbeot_service.serve(websocket, mode)
