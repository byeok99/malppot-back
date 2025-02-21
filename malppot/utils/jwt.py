import jwt
import datetime

class JWTService:
    def __init__(self, secret_key:str, access_token_expire_minutes: int, refresh_token_expire_days: int, algorithm: str):
        self.secret_key = secret_key
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.algorithm = algorithm

    def create_access_token(self, user_id) -> str:
        payload = {
            "sub": user_id,
            "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=self.access_token_expire_minutes),
            "iat": datetime.datetime.now(datetime.UTC),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id) -> str:
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