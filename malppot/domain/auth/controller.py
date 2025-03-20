from http.client import HTTPException
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Request, HTTPException, Response
from malppot.domain.auth.schema import LoginRequest, RegisterRequest
from malppot.di import DI

router = APIRouter()

@router.post("/login")
@inject
async def login(
        login_data: LoginRequest,
        response: Response,
        auth_service=Provide[DI.auth.service],  # : AuthService..
        jwt_service=Provide[DI.jwt_service],
) -> dict[str, str]:
    _id, _pw = login_data.id, login_data.pw
    user = auth_service.get_user_by_id(_id)
    if user is None or not auth_service.verify_password(_pw, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = jwt_service.create_access_token(user.id)
    refresh_token = jwt_service.create_refresh_token(user.id)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # HTTPS 환경에서는 True
        samesite="Strict",  # CSRF 방어
    )
    return {"access_token": access_token}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("refresh_token")
    return {"message": "Successfully logged out"}

@router.post("/refresh")
@inject
async def refresh(
    request: Request,
    jwt_service=Provide[DI.jwt_service],
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    payload = jwt_service.verify_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    new_access_token = jwt_service.create_access_token(payload["sub"])

    return {"access_token": new_access_token}

@router.post("/register")
@inject
async def register(
    data: RegisterRequest,
    auth_service=Provide[DI.auth.service],  # : AuthService..
):
    if not all([data.name, data.email, data.id, data.password, data.gender]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    try:
        user = auth_service.register_user(
            name=data.name,
            email=data.email,
            id=data.id,
            password=data.password,
            gender=data.gender
        )
        return {"message": "User registered successfully", "user_idx": user.user_idx}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))