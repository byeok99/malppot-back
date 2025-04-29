from dependency_injector import containers, providers
from malppot.conf.db import DatabaseSession
from malppot.domain.pronunciation.service import PronunciationService


class _PronunciationContainer(containers.DeclarativeContainer):
    db = providers.Dependency(instance_of=DatabaseSession)
    config = providers.Dependency()

    service = providers.Factory(
        PronunciationService,
        db=db.provided,
        config=config.provided,
    )