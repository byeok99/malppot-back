from pydantic import BaseModel

class UserInfoResponse(BaseModel):
    name: str
    email: str
    profile_image_url: str

class LoginResponse(BaseModel):
    access_token: str
    user_info: UserInfoResponse

__all__ = (
    'LoginResponse',
)