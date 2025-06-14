from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship
from malppot.conf.db_base import Base

class User(Base):
    __tablename__ = 'users'

    user_idx = Column(Integer, primary_key=True, autoincrement=True)
    google_id = Column(String(50), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    name = Column(String(100))
    profile_image_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

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