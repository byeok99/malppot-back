from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from malppot.conf.settings import DBConfig


class DatabaseSession:
    def __init__(self, config: DBConfig):
        if isinstance(config, dict):
            config = DBConfig(**config)

        self.driver = config.driver
        self.user = config.user
        self.password = config.password
        self.host = config.host
        self.port = config.port
        self.name = config.name

        self.DATABASE_URL = f"{self.driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

        self.engine = create_engine(self.DATABASE_URL, pool_pre_ping=True, pool_recycle=1800, echo=False)

        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        self.Base = declarative_base()

    def get_session(self):
        return self.SessionLocal()

    def create_all(self):
        self.Base.metadata.create_all(bind=self.engine)
