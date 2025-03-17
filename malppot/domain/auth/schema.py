from pydantic import BaseModel

class LoginRequest(BaseModel):
    id: str
    pw: str

class RegisterRequest(BaseModel):
    name: str
    email: str
    id: str
    password: str
    gender: str

__all__ = (
    'LoginRequest',
    'RegisterRequest',
)