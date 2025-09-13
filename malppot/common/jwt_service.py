import datetime

import jwt

from malppot.conf.settings import JWTConfig


class JWTService:
    def __init__(self, config: JWTConfig | dict):
        if isinstance(config, dict):
            config = JWTConfig(**config)

        self.secret_key = config.secret_key
        self.access_token_expire_minutes = config.access_token_expire_minutes
        self.refresh_token_expire_days = config.refresh_token_expire_days
        self.algorithm = config.algorithm

    def create_access_token(self, user_id: int) -> str:
        payload = {
            "sub": user_id,
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
                minutes=self.access_token_expire_minutes),
            "iat": datetime.datetime.now(datetime.timezone.utc),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: int) -> str:
        payload = {
            "sub": user_id,
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
                days=self.refresh_token_expire_days),
            "iat": datetime.datetime.now(datetime.timezone.utc),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str):
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def get_user_id(self, token: str) -> int | None:
        payload = self.verify_token(token)
        if payload:
            return payload.get("sub")
        return None
