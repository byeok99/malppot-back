import httpx
from fastapi import APIRouter, Request, Response, Depends

from malppot.common.di_providers import (
    get_auth_service_from_di,
    get_jwt_service_from_di,
    get_speech_service_from_di
)
from malppot.common.errors import (
    MissingAuthCodeException,
    FailedGoogleAccessTokenException,
    FailedGoogleUserInfoException,
    InvalidCredentialsException,
    InvalidTokenException
)
from malppot.domain.auth.schema import LoginResponse

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
        request: Request,
        response: Response,
        auth_service=Depends(get_auth_service_from_di),
        jwt_service=Depends(get_jwt_service_from_di),
        speech_service=Depends(get_speech_service_from_di)
) -> dict[str, str]:
    info = auth_service.get_google_auth_info()

    google_client_id = info.client_id
    google_client_secret = info.client_secret
    google_client_uri = info.redirect_uri

    data = await request.json()
    code = data.get("code")

    if not code:
        raise MissingAuthCodeException()

    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": google_client_id,
                "client_secret": google_client_secret,
                "redirect_uri": google_client_uri,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if token_res.status_code != 200:
        raise FailedGoogleAccessTokenException()

    access_token_from_google = token_res.json().get("access_token")

    async with httpx.AsyncClient() as client:
        user_res = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token_from_google}"}
        )

    if user_res.status_code != 200:
        raise FailedGoogleUserInfoException()

    user_info = user_res.json()
    google_id = user_info.get("id")
    email = user_info.get("email")
    name = user_info.get("name")
    profile_image_url = user_info.get("picture")

    user = auth_service.get_user_by_id(google_id)
    if not user:
        auth_service.register_user(google_id, email, name, profile_image_url)
        user = auth_service.get_user_by_id(google_id)

    access_token = jwt_service.create_access_token(user.google_id)
    refresh_token = jwt_service.create_refresh_token(user.google_id)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="Strict"
    )

    return {
        "access_token": access_token,
        "user_info": {
            "name": user.name,
            "email": user.email,
            "profile_image_url": user.profile_image_url
        }
    }


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("refresh_token")
    return {"message": "Successfully logged out"}


@router.post("/refresh")
async def refresh(
        request: Request,
        jwt_service=Depends(get_jwt_service_from_di),
):
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise InvalidCredentialsException(detail="Refresh token not found in cookies.")

    payload = jwt_service.verify_token(refresh_token)

    if not payload:
        raise InvalidTokenException(detail="Invalid or expired refresh token.")

    new_access_token = jwt_service.create_access_token(payload["sub"])

    return {"access_token": new_access_token}
