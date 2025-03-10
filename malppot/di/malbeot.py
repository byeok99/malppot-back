from dependency_injector import containers, providers
from malppot.conf.db import DatabaseSession
from malppot.domain.malbeot.service import MalbeotService


class _MalbeotContainer(containers.DeclarativeContainer):
    db = providers.Dependency(instance_of=DatabaseSession)
    config = providers.Dependency()

    service = providers.Factory(
        MalbeotService,
        db=db.provided,
        config=config.provided,
    )