from fastapi import FastAPI
from malppot.di import DI
from malppot.domain.auth.controller import router as auth_router, login
from malppot.domain.malbeot.controller import router as malbeot_router
from malppot.domain.pronunciation.controller import router as pronunciation_router
from malppot.domain.heygen.controller import router as heygen_router

def create_app() -> FastAPI:
    app = FastAPI(
        debug=True,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # DI Container 초기화
    di_container = DI()
    di_container.init_resources()
    di_container.wire(modules=[
        "malppot.domain.auth.controller",
        "malppot.domain.malbeot.controller",
        "malppot.domain.pronunciation.controller",
        "malppot.domain.heygen.controller"
    ])

    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(malbeot_router, prefix="/malbeot", tags=["malbeot"])
    app.include_router(pronunciation_router, prefix="/pronunciation", tags=["pronunciation"])
    app.include_router(heygen_router, prefix="/heygen", tags=["heygen"])

    return app

__all__ = (
    "create_app",
)