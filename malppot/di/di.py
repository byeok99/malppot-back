from dependency_injector import containers, providers
from malppot.di.config import ConfigContainer
from malppot.conf.db import DatabaseSession
from malppot.di.auth import _AuthContainer
from malppot.di.malbeot import _MalbeotContainer
from malppot.utils.jwt import JWTService

class DI(containers.DeclarativeContainer):
    config = providers.Container(ConfigContainer).config

    db = providers.Singleton(
        DatabaseSession,
        config = config.db,
    )

    jwt_service = providers.Singleton(
        JWTService,
        config=config.jwt,
    )

    auth = providers.Container(
        _AuthContainer,
        db=db,
    )

    malbeot = providers.Container(
        _MalbeotContainer,
        config=config.openai,
        db=db,
    )


__all__ = (
    'DI',
)