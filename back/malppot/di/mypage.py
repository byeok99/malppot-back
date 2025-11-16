from dependency_injector import containers, providers

from malppot.conf.db import DatabaseSession
from malppot.domain.mypage.service import MyPageService
from malppot.domain.recommendation.service import RecommendationService


class _MyPageContainer(containers.DeclarativeContainer):
    db = providers.Dependency(instance_of=DatabaseSession)

    recommendation_service = providers.Dependency(instance_of=RecommendationService)
    service = providers.Factory(
        MyPageService,
        db=db.provided,
        recommendation_service=recommendation_service,
    )
