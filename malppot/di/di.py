from dependency_injector import containers, providers
from malppot.di.config import ConfigContainer
from malppot.conf.db import DatabaseSession
from malppot.di.auth import _AuthContainer
from malppot.di.malbeot import _MalbeotContainer
from malppot.utils.jwt import JWTService
from malppot.domain.pronunciation.service import PronunciationService
from malppot.domain.heygen.service import HeyGenService 

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
    
    azure_speech_service = providers.Singleton(
        PronunciationService,
        config=config.azure_speech,
    )

    heygen_service = providers.Singleton(
        HeyGenService,
        api_key=config.heygen.api_key,
        base_url=config.heygen.base_url,
    )

__all__ = (
    'DI',
)