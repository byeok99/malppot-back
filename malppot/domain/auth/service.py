from typing import Optional

from passlib.context import CryptContext

from malppot.conf.settings import GoogleConfig
from malppot.domain.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, config, db):
        if isinstance(config, dict):
            config = GoogleConfig(**config)
        self.config = config
        self.db = db

    def get_user_by_id(self, _id: str) -> Optional[User]:
        session = self.db.get_session()
        user = session.query(User).filter(User.google_id == _id).first()
        session.close()
        return user

    def verify_password(self, origin_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(origin_password, hashed_password)

    def create_hashed_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def get_google_auth_info(self) -> dict:
        return self.config

    def register_user(self, google_id, email, name, profile_image_url):
        session = self.db.get_session()
        try:
            existing_user = session.query(User).filter(User.google_id == google_id).first()
            if existing_user:
                raise ValueError(f"User with google_id {google_id} already exists")

            existing_email = session.query(User).filter(User.email == email).first()
            if existing_email:
                raise ValueError(f"User email {email} already exists")

            new_user = User(
                google_id=google_id,
                email=email,
                name=name,
                profile_image_url=profile_image_url
            )
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            return new_user
        finally:
            session.close()
