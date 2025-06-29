from dependency_injector import containers, providers

from malppot.common.gpt_service import GPTService
from malppot.conf.db import DatabaseSession
from malppot.domain.recommendation.service import RecommendationService


class _RecommendationContainer(containers.DeclarativeContainer):
    db = providers.Dependency(instance_of=DatabaseSession)
    gpt_service = providers.Dependency(instance_of=GPTService)

    service = providers.Factory(
        RecommendationService,
        gpt_service=gpt_service.provided,
        db=db.provided,
    )
