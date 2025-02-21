from pathlib import Path
from dependency_injector import containers, providers
from malppot.conf.settings import DBConfig, JWTConfig, OpenAIConfig, Config

class ConfigContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    config.from_yaml(
        str(Path(__file__).parent.parent/"config.yaml"),
        required=True
    )
    config.from_dict(
        Config(
            db = DBConfig(
                host= config.db.host(),
                port= config.db.port(),
                user= config.db.user(),
                password= config.db.password(),
                name= config.db.name(),
                driver= config.db.driver()
            ),
            jwt = JWTConfig(
                secret_key= config.jwt.secret_key(),
                access_token_expire_minutes= config.jwt.access_token_expire_minutes(),
                refresh_token_expire_days= config.jwt.refresh_token_expire_days(),
                algorithm= config.jwt.algorithm(),
            ),
            openAI = OpenAIConfig(
                api_key= config.openai.api_key(),
            )
        ).model_dump()
    )


__all__ = {
    'ConfigContainer'
}