from http.client import HTTPException
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Request, HTTPException, Response
from malppot.domain.auth.schema import LoginResponse
from malppot.di import DI
import httpx

router = APIRouter()

@router.post("/login", response_model=LoginResponse)
@inject
async def login(
        request: Request,
        response: Response,
        auth_service=Provide[DI.auth.service],  # : AuthService..
        jwt_service=Provide[DI.jwt_service],
) -> dict[str, str]:
    info = auth_service.get_google_auth_info()

    GOOGLE_CLIENT_ID = info.client_id
    GOOGLE_CLIENT_SECRET = info.client_secret
    GOOGLE_REDIRECT_URI = info.redirect_uri

    data = await request.json()
    code = data.get("code")

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    # 1. code로 access_token 받기
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if token_res.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get access token from Google")

    access_token_from_google = token_res.json().get("access_token")

    # 2. access_token으로 사용자 정보 조회
    async with httpx.AsyncClient() as client:
        user_res = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token_from_google}"}
        )

    if user_res.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get user info from Google")

    user_info = user_res.json()
    google_id = user_info.get("id")
    email = user_info.get("email")
    name = user_info.get("name")

    # 3. 사용자 DB 확인 및 등록/갱신
    user = auth_service.get_user_by_id(google_id)
    if not user:
        user = auth_service.register_user(google_id, email, name)

    # 4. 내부 access, refresh 토큰 생성
    access_token = jwt_service.create_access_token(user.google_id)
    refresh_token = jwt_service.create_refresh_token(user.google_id)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # HTTPS 환경이면 True
        samesite="Strict"
    )

    return {
        "access_token": access_token,
        "user_info": {
            "name": user.name,
            "email": user.email
        }
    }

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("refresh_token")
    return {"message": "Successfully logged out"}

# 만료시 다른 곳으로 보내야댐..
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