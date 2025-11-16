from dependency_injector import containers, providers

from malppot.common.gpt_service import GPTService
from malppot.conf.db import DatabaseSession
from malppot.domain.recommendation.service import RecommendationService
from malppot.domain.speech.service import SpeechService


class _RecommendationContainer(containers.DeclarativeContainer):
    db = providers.Dependency(instance_of=DatabaseSession)
    gpt_service = providers.Dependency(instance_of=GPTService)
    speech_service = providers.Dependency(instance_of=SpeechService)

    service = providers.Factory(
        RecommendationService,
        gpt_service=gpt_service.provided,
        speech_service=speech_service.provided,
        db=db.provided,
    )
