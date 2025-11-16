import json
from typing import List, Dict
from uuid import uuid4

from sqlalchemy.orm import Session

from malppot.common.gpt_service import GPTService
from malppot.domain.models import RecommendationsWords
from malppot.domain.speech.service import SpeechService
from malppot.utils.datetime_utils import now_kst


class RecommendationService:
    def __init__(self, db, gpt_service: GPTService, speech_service: SpeechService):
        self.db = db
        self.gpt_service = gpt_service
        self.speech_service = speech_service

    # 추천 단어 생성해서 저장하는 코드
    async def save_recommendation_words(self, jamo: str) -> None:
        session: Session = self.db.get_session()

        try:
            words: list[dict[str, str]] = await self.gpt_service.ask_recommendation_word(jamo, 4)
            print(words)
            for word in words:
                await self.speech_service.convert(word.get('sentence'))

            # 이미 존재하면 덮어쓰고, 없으면 새로 삽입
            existing = session.query(RecommendationsWords).filter_by(jamo_initial=jamo).first()
            if existing:
                existing.words = words
                existing.created_at = now_kst()
            else:
                session.add(
                    RecommendationsWords(
                        id=str(uuid4()),
                        jamo_initial=jamo,
                        words=words,
                        created_at=now_kst(),
                    )
                )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_words(self, jamo_initial: str) -> List[Dict[str, str]]:
        """
        해당 초성의 단어+문장 리스트를 반환한다.
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
            # words가 이미 파싱된 list[dict]면 그대로, 아니면 json 파싱
            result = words if isinstance(words, list) else json.loads(words)

            if isinstance(result, list) and all(
                    isinstance(x, dict) and 'word' in x and 'sentence' in x for x in result):
                return result
            raise ValueError("데이터 포맷 오류: 기대한 리스트[dict]가 아님")
        finally:
            db.close()
