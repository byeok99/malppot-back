from pathlib import Path

from dependency_injector import containers, providers

from malppot.conf.settings import DBConfig, JWTConfig, OpenAIConfig, AzureSpeechConfig, HeyGenConfig, Config, \
    GoogleConfig


class ConfigContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    config.from_yaml(
        str(Path(__file__).parent.parent / "config.yaml"),
        required=True
    )

    config.from_dict(
        Config(
            db=DBConfig(
                host=config.db.host(),
                port=config.db.port(),
                user=config.db.user(),
                password=config.db.password(),
                name=config.db.name(),
                driver=config.db.driver()
            ),
            jwt=JWTConfig(
                secret_key=config.jwt.secret_key(),
                access_token_expire_minutes=config.jwt.access_token_expire_minutes(),
                refresh_token_expire_days=config.jwt.refresh_token_expire_days(),
                algorithm=config.jwt.algorithm(),
            ),
            openai=OpenAIConfig(
                api_key=config.openai.api_key(),
                realtime_model=config.openai.realtime_model(),
                text_model=config.openai.text_model(),
                url=config.openai.url(),
            ),
            azure_speech=AzureSpeechConfig(
                azure_key=config.azure_speech.azure_key(),
                azure_region=config.azure_speech.azure_region(),
                replicate_key=config.azure_speech.replicate_key()
            ),
            heygen=HeyGenConfig(
                api_key=config.heygen.api_key(),
                base_url=config.heygen.base_url(),
                avatar_id=config.heygen.avatar_id(),
                voice_id=config.heygen.voice_id(),
                callback_url=config.heygen.callback_url(),
            ),
            google=GoogleConfig(
                client_id=config.google.client_id(),
                client_secret=config.google.client_secret(),
                redirect_uri=config.google.redirect_uri(),
            )
        ).model_dump()
    )


__all__ = {
    'ConfigContainer'
}
