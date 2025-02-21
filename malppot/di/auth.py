from dependency_injector import containers, providers
from malppot.conf.db import DatabaseSession
from malppot.domain.auth.service import AuthService


class _AuthContainer(containers.DeclarativeContainer):
    db = providers.Dependency(instance_of=DatabaseSession)

    service = providers.Factory(
        AuthService,
        db=db.provided,
    )