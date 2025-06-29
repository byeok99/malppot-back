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
    realtime_model: str
    text_model: str
    url: str


class AzureSpeechConfig(BaseSettings):
    azure_key: str
    azure_region: str
    replicate_key: str


class HeyGenConfig(BaseSettings):
    api_key: str
    base_url: str
    avatar_id: str
    voice_id: str
    callback_url: str


class GoogleConfig(BaseSettings):
    client_id: str
    client_secret: str
    redirect_uri: str


class Config(BaseSettings):
    db: DBConfig
    jwt: JWTConfig
    openai: OpenAIConfig
    azure_speech: AzureSpeechConfig
    heygen: HeyGenConfig
    google: GoogleConfig


__all__ = (
    'DBConfig',
    'JWTConfig',
    'OpenAIConfig',
    'AzureSpeechConfig',
    'GoogleConfig',
    'HeyGenConfig',
    'Config',
)
