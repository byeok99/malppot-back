import jwt
import datetime
from malppot.conf.settings import JWTConfig

class JWTService:
    def __init__(self, config:JWTConfig | dict):
        if isinstance(config, dict):
            config = JWTConfig(**config)

        self.secret_key = config.secret_key
        self.access_token_expire_minutes = config.access_token_expire_minutes
        self.refresh_token_expire_days = config.refresh_token_expire_days
        self.algorithm = config.algorithm

    def create_access_token(self, user_id:int) -> str:
        payload = {
            "sub": user_id,
            "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=self.access_token_expire_minutes),
            "iat": datetime.datetime.now(datetime.UTC),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id:int) -> str:
        payload = {
            "sub": user_id,
            "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=self.refresh_token_expire_days),
            "iat": datetime.datetime.now(datetime.UTC),
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

    def get_items(self, token):
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

    def get_user_id(self, token: str) -> str | None:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload.get("sub")
        except jwt.ExpiredSignatureError:
            print("Expired token")
            return None
        except jwt.InvalidTokenError:
            print("Invalid token")
            return None