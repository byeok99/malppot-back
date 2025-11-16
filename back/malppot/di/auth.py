from dependency_injector import containers, providers

from malppot.conf.db import DatabaseSession
from malppot.domain.auth.service import AuthService


class _AuthContainer(containers.DeclarativeContainer):
    db = providers.Dependency(instance_of=DatabaseSession)
    config = providers.Dependency()

    service = providers.Factory(
        AuthService,
        config=config.provided,
        db=db.provided,
    )
