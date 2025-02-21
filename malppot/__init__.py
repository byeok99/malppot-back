from fastapi import FastAPI
from malppot.di import DI
from malppot.domain.auth.controller import router as auth_router

def create_app() -> FastAPI:
    app = FastAPI(debug=True)

    # # DI Container 초기화
    di_container = DI()
    di_container.init_resources()
    di_container.wire(modules=[auth_router])

    # config = di_container.config
    # print(config['db'].host)


    app.include_router(auth_router, prefix="/auth", tags=["auth"])

    return app

__all__ = (
    "create_app",
)