import enum
from sqlalchemy import Column, DateTime, Integer, String, Enum
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel

Base = declarative_base()

class LoginRequest(BaseModel):
    id: str
    pw: str

class RegisterRequest(BaseModel):
    name: str
    email: str
    id: str
    password: str
    gender: str

class Gender(str, enum.Enum):
    W="W"
    M="M"

class Role(str, enum.Enum):
    User="User"
    Admin="Admin"

class User(Base):
    __tablename__ = 'users'

    user_idx = Column(Integer, primary_key=True)
    id = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    username = Column(String(20), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    gender = Column(Enum('W', 'M'))
    join_date = Column(DateTime(timezone=True), server_default=func.now())
    role = Column(Enum('User', 'Admin'))

    def __hash__(self) -> hash:
        return hash(self.user_idx)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return False
        return self.user_idx == other.user_idx

__all__ = (
    'User',
    'RegisterRequest',
    'LoginRequest',
)