import datetime
import json
from typing import List
from uuid import uuid4

from sqlalchemy.orm import Session

from malppot.common.gpt_service import GPTService
from malppot.domain.models import RecommendationsWords


class RecommendationService:
    def __init__(self, db, gpt_service: GPTService):
        self.db = db
        self.gpt_service = gpt_service

    # 추천 단어 생성해서 저장하는 코드
    async def save_recommendation_words(self, jamos: list[str]) -> None:
        session: Session = self.db.get_session()

        try:
            for jamo in jamos:
                words: list[str] = await self.gpt_service.ask_recommendation_word(jamo, 4)

                # 이미 존재하면 덮어쓰고, 없으면 새로 삽입
                existing = session.query(RecommendationsWords).filter_by(jamo_initial=jamo).first()
                if existing:
                    existing.words = words
                    existing.created_at = datetime.datetime.utcnow()
                else:
                    session.add(
                        RecommendationsWords(
                            id=str(uuid4()),
                            jamo_initial=jamo,
                            words=words,
                            created_at=datetime.datetime.utcnow(),
                        )
                    )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_words(self, jamo_initial: str) -> List[str]:
        """
        해당 초성의 단어 리스트를 반환한다.
        레코드가 없으면 [] 리턴.
        """
        db: Session = self.db.get_session()
        try:
            row = (
                db.query(RecommendationsWords.words)
                .filter(RecommendationsWords.jamo_initial == jamo_initial)
                .first()
            )
            if not row:
                return []
            words = row[0]  # .words 컬럼만 선택했으므로 튜플
            return words if isinstance(words, list) else json.loads(words)
        finally:
            db.close()
