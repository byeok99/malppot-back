from fastapi import FastAPI
from malppot.di import DI
from malppot.domain.auth.controller import router as auth_router, login
from malppot.domain.malbeot.controller import router as malbeot_router

def create_app() -> FastAPI:
    app = FastAPI(debug=True)

    # # DI Container 초기화
    di_container = DI()
    di_container.init_resources()
    di_container.wire(modules=[
        "malppot.domain.auth.controller",
        "malppot.domain.malbeot.controller"
    ])

    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(malbeot_router, prefix="/malbeot", tags=["malbeot"])

    return app

__all__ = (
    "create_app",
)