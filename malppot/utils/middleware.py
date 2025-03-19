from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
from starlette.responses import JSONResponse
from malppot.di import DI


class JWTMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.secret_key = DI.config.jwt.secret_key
        self.algorithm = DI.config.jwt.algorithm

    async def dispatch(self, request: Request, call_next):
        # open_paths = ["/auth", "/docs"]
        open_paths = ["/auth", "/docs", "/redoc", "/openapi.json"]

        if any(request.url.path.startswith(path) for path in open_paths):
            return await call_next(request)

        token = request.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            token = token.split(" ")[1]
            try:
                payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
                request.state.user = payload["sub"]
            except jwt.ExpiredSignatureError:
                return JSONResponse({"detail": "Token expired"}, status_code=401)
            except jwt.InvalidTokenError:
                return JSONResponse({"detail": "Invalid token"}, status_code=401)

        else:
            return JSONResponse({"detail": "Authorization hearder missing"}, status_code=401)

        return await call_next(request)
