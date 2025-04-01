from dependency_injector import containers, providers
from malppot.conf.db import DatabaseSession
from malppot.domain.heygen.service import HeyGenService


class _HeygenContainer(containers.DeclarativeContainer):
    db = providers.Dependency(instance_of=DatabaseSession)
    config = providers.Dependency()

    service = providers.Factory(
        HeyGenService,
        db=db.provided,
        config=config.provided,
    )