from dependency_injector import containers, providers

from malppot.conf.db import DatabaseSession
from malppot.domain.malbeot.service import MalbeotService
from malppot.domain.mypage.service import MyPageService


class _MalbeotContainer(containers.DeclarativeContainer):
    db = providers.Dependency(instance_of=DatabaseSession)
    config = providers.Dependency()

    mypage_service = providers.Dependency(instance_of=MyPageService)
    service = providers.Factory(
        MalbeotService,
        db=db.provided,
        config=config.provided,
        mypage_service=mypage_service.provided,
    )
