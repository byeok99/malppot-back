from dependency_injector import containers, providers

from malppot.common.gpt_service import GPTService
from malppot.conf.db import DatabaseSession
from malppot.domain.speech.service import SpeechService


class _SpeechContainer(containers.DeclarativeContainer):
    db = providers.Dependency(instance_of=DatabaseSession)
    config = providers.Dependency()
    gpt_service = providers.Dependency(instance_of=GPTService)

    service = providers.Factory(
        SpeechService,
        db=db.provided,
        config=config.provided,
        gpt_service=gpt_service.provided,
    )
