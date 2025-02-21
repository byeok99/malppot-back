from pydantic_settings import BaseSettings

class DBConfig(BaseSettings):
    host: str
    port: int
    user: str
    password: str
    name: str
    driver: str

class JWTConfig(BaseSettings):
    secret_key: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    algorithm: str

class OpenAIConfig(BaseSettings):
    api_key: str

class Config(BaseSettings):
    db: DBConfig
    jwt: JWTConfig
    openAI: OpenAIConfig

__all__ = (
    'DBConfig',
    'JWTConfig',
    'OpenAIConfig',
    'Config',
)
