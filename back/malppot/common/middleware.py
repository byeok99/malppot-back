import logging

import jwt
from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from malppot.di import DI

logger = logging.getLogger(__name__)


class JWTMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.secret_key = DI.config.jwt.secret_key()
        self.algorithm = DI.config.jwt.algorithm()

    async def dispatch(self, request: Request, call_next):
        open_paths = ["/auth", "/docs", "/redoc", "/openapi.json", "/static"]
        if any(request.url.path.startswith(path) for path in open_paths):
            return await call_next(request)

        token = request.headers.get("Authorization")
        print(request)
        if token and token.startswith("Bearer "):
            token = token.split(" ")[1]
            try:
                payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
                request.state.user = payload["sub"]

            except jwt.ExpiredSignatureError:
                logger.warning(f"JWT: Token expired for path {request.url.path}")
                return JSONResponse({"detail": "Token expired"}, status_code=status.HTTP_401_UNAUTHORIZED)
            except jwt.InvalidTokenError:
                logger.warning(f"JWT: Invalid token for path {request.url.path}")
                return JSONResponse({"detail": "Invalid token"}, status_code=status.HTTP_401_UNAUTHORIZED)
            except Exception as e:
                logger.exception(
                    f"JWT: Unexpected error during token decoding for path {request.url.path}: {e}")
                return JSONResponse({"detail": "Token processing error"}, status_code=status.HTTP_401_UNAUTHORIZED)
        else:
            logger.warning(f"JWT: Authorization header missing or malformed for path {request.url.path}")
            return JSONResponse({"detail": "Authorization header missing"}, status_code=status.HTTP_401_UNAUTHORIZED)

        return await call_next(request)
