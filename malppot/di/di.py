from dependency_injector import containers, providers
from malppot.di.config import ConfigContainer
from malppot.conf.db import DatabaseSession
from malppot.di.auth import _AuthContainer
from malppot.utils.jwt import JWTService

class DI(containers.DeclarativeContainer):
    config = providers.Container(ConfigContainer).config

    db = providers.Singleton(
        DatabaseSession,
        db_driver=config.db.driver,
        db_user=config.db.user,
        db_password=config.db.password,
        db_host=config.db.host,
        db_port=config.db.port,
        db_name=config.db.name,
    )

    jwt_service = providers.Singleton(
        JWTService,
        secret_key=config.jwt.secret_key,
        access_token_expire_minutes=config.jwt.access_token_expire_minutes,
        refresh_token_expire_days=config.jwt.refresh_token_expire_days,
        algorithm=config.jwt.algorithm,
    )

    auth = providers.Container(
        _AuthContainer,
        db=db,
    )
    #
    # # ✅ MalbeotContainer를 포함 (DB 및 OpenAI API 키 주입)
    # malbeot = providers.Container(
    #     _MalbeotContainer,
    #     db=db.provided,
    #     api_key=config.provided.openai.api_key,
    # )


__all__ = (
    'DI',
)