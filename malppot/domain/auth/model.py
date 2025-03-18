import enum
from sqlalchemy import Column, DateTime, Integer, String, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from malppot.conf.db_base import Base

class User(Base):
    __tablename__ = 'users'

    user_idx = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    username = Column(String(20), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    gender = Column(Enum('w', 'm'))
    join_date = Column(DateTime(timezone=True), server_default=func.now())
    role = Column(Enum('user', 'admin'))

    ai_malbeot_logs = relationship("AIMalbeotLog", back_populates="user")

    def __hash__(self) -> hash:
        return hash(self.user_idx)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return False
        return self.user_idx == other.user_idx

__all__ = (
    'User',
)