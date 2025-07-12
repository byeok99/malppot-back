from dependency_injector import containers, providers

from malppot.common.gpt_service import GPTService
from malppot.common.jwt_service import JWTService
from malppot.conf.db import DatabaseSession
from malppot.di.auth import _AuthContainer
from malppot.di.config import ConfigContainer
from malppot.di.game import _GameContainer
from malppot.di.malbeot import _MalbeotContainer
from malppot.di.mypage import _MyPageContainer
from malppot.di.recommendation import _RecommendationContainer
from malppot.di.speech import _SpeechContainer


class DI(containers.DeclarativeContainer):
    config = providers.Container(ConfigContainer).config

    db = providers.Singleton(
        DatabaseSession,
        config=config.db,
    )

    jwt_service = providers.Singleton(
        JWTService,
        config=config.jwt,
    )

    gpt_service = providers.Singleton(
        GPTService,
        config=config.openai,
    )

    auth = providers.Container(
        _AuthContainer,
        config=config.google,
        db=db,
    )

    speech = providers.Container(
        _SpeechContainer,
        config=config.azure_speech,
        db=db,
        gpt_service=gpt_service,
    )

    recommendation = providers.Container(
        _RecommendationContainer,
        db=db,
        gpt_service=gpt_service,
        speech_service=speech.service,
    )

    mypage = providers.Container(
        _MyPageContainer,
        db=db,
        recommendation_service=recommendation.service
    )

    malbeot = providers.Container(
        _MalbeotContainer,
        config=config.openai,
        db=db,
        mypage_service=mypage.service,
    )

    game = providers.Container(
        _GameContainer,
        db=db,
        gpt_service=gpt_service,
    )


__all__ = (
    'DI',
)
