import sys
from pathlib import Path

from dependency_injector import wiring
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from malppot.common.errors import CustomException
from malppot.di import DI

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "https://www.malppot.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# app.add_middleware(JWTMiddleware)

app.mount("/static", StaticFiles(directory=f"{PROJECT_ROOT}/malppot/static"), name="static")

container = DI()

import malppot.domain.auth.controller
import malppot.common.dependencies
import malppot.domain.malbeot.controller
import malppot.domain.speech.controller
import malppot.domain.mypage.controller
import malppot.domain.game.controller

wiring.wire(
    container=container,
    modules=[
        malppot.common.dependencies,
        malppot.domain.auth.controller,
        malppot.domain.malbeot.controller,
        malppot.domain.speech.controller,
        malppot.domain.mypage.controller,
        malppot.domain.game.controller,
    ]
)


@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail, "code": exc.status_code},
    )


# 라우터 연결 (이전 제안과 동일)
from malppot.domain.auth.controller import router as auth_router
from malppot.domain.malbeot.controller import router as malbeot_router
from malppot.domain.speech.controller import router as speech_router
from malppot.domain.mypage.controller import router as mypage_router
from malppot.domain.game.controller import router as game_router

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(malbeot_router, prefix="/malbeot", tags=["malbeot"])
app.include_router(speech_router, prefix="/speech", tags=["speech"])
app.include_router(mypage_router, prefix="/mypage", tags=["mypage"])
app.include_router(game_router, prefix="/game", tags=["game"])
