import datetime
from typing import Optional
from passlib.context import CryptContext
from malppot.domain.auth.model import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, db):
        self.db_provider = db

    def get_user_by_id(self, _id:str) -> Optional[User]:
        session = self.db_provider.get_session()
        return session.query(User).filter(User.id == _id).first()

    def verify_password(self, origin_password:str, hashed_password:str) -> bool:
        return pwd_context.verify(origin_password, hashed_password)

    def create_hashed_password(self, password:str) -> str:
        return pwd_context.hash(password)

    def register_user(self, name, email, id, password, gender):
        session = self.db_provider.get_session()
        if session.query(User).filter(User.id == id).first():
            raise ValueError("User id is already exist")
        if session.query(User).filter(User.email == email).first():
            raise ValueError("User email is already exist")

        hashed_password = self.create_hashed_password(password)
        new_user = User(
            id=id,
            username=name,
            email=email,
            password=hashed_password,
            gender=gender,
            join_date=datetime.datetime.now(datetime.UTC)
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        return new_user