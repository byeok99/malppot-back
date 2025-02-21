from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

class DatabaseSession :
    def __init__(self,
                 db_driver: str,
                 db_user: str,
                 db_password: str,
                 db_host: str,
                 db_port: int,
                 db_name: str
                 ):

        self.db_driver = db_driver
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name

        self.DATABASE_URL = f"{self.db_driver}://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

        self.engine = create_engine(self.DATABASE_URL, echo=True)

        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        self.Base = declarative_base()

    def get_session(self):
        return self.SessionLocal()

    def create_all(self):
        self.Base.metadata.create_all(bind=self.engine)