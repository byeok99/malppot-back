from sqlalchemy import Column, Integer, Enum, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from malppot.conf.db_base import Base

class AIMalbeotLog(Base):
    __tablename__ = "ai_malbeot_logs"

    log_idx = Column(Integer, primary_key=True, autoincrement=True)
    user_idx = Column(Integer, ForeignKey("users.user_idx", ondelete="CASCADE"), nullable=False)
    session_id = Column(Integer, nullable=False)
    speaker = Column(Enum("user", "model"), nullable=False)
    chat_text = Column(Text, nullable=False)
    created_date = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="ai_malbeot_logs", lazy="joined")

    def __hash__(self) -> hash:
        return hash(self.log_idx)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AIMalbeotLog):
            return False
        return self.log_idx == other.log_idx

__all__ = (
    "AIMalbeotLog",
)