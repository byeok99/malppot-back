from fastapi import Request, Depends
from fastapi import WebSocket

from malppot.common.di_providers import get_jwt_service_from_di, get_auth_service_from_di
from malppot.common.errors import (
    InvalidTokenException,
    UserNotFoundException,
    AuthenticationTokenMissingException,
)
from malppot.domain.models import User


def get_current_user(
        request: Request,
        jwt_service=Depends(get_jwt_service_from_di),
        auth_service=Depends(get_auth_service_from_di),
) -> User:
    auth_header = request.headers.get("Authorization")
    token = auth_header.replace("Bearer ", "").strip() if auth_header else None

    if not token:
        raise AuthenticationTokenMissingException()

    user_id = jwt_service.get_user_id(token)
    if user_id is None:
        raise InvalidTokenException()

    user = auth_service.get_user_by_id(user_id)
    if user is None:
        raise UserNotFoundException()

    return user


def get_current_user_ws(websocket: WebSocket) -> User:
    jwt_service = get_jwt_service_from_di()
    auth_service = get_auth_service_from_di()

    token = websocket.query_params.get("access_token")
    if not token:
        raise AuthenticationTokenMissingException()
    
    user_id = jwt_service.get_user_id(token)
    if user_id is None:
        raise InvalidTokenException()

    user = auth_service.get_user_by_id(user_id)
    if user is None:
        raise UserNotFoundException()

    return user
