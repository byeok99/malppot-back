from datetime import datetime
from typing import List, Set

from sqlalchemy import select, distinct, func
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

from malppot.common.errors import CustomException
from malppot.common.gpt_service import GPTService
from malppot.domain.game.schema import StageData
from malppot.domain.models import (
    Word,
    RecommendationsWords,
    PracticeSession,
    PracticeWord,
    UserStageProgress,
    StageWords,
    EndlessScores
)


class GameService:
    def __init__(self, db, gpt_service: GPTService):
        self.db = db
        self.gpt_service = gpt_service

    async def get_endless_word_pool(self, user_idx: int) -> List[str]:
        session: Session = self.db.get_session()

        words_from_db: List[str] = await self._get_user_practiced_words(user_idx)

        stmt_reco = select(RecommendationsWords.words)
        reco_rows = session.scalars(stmt_reco).all()

        words_from_reco: List[str] = []
        for word_list in reco_rows:
            # word_list는 [{ "word": "뜻밖", "sentence": ... }, ...] 또는 문자열(JSON)일 수 있음
            if isinstance(word_list, str):
                import json
                word_list = json.loads(word_list)
            # word_list가 리스트일 때만 처리
            if isinstance(word_list, list):
                for item in word_list:
                    if isinstance(item, dict) and 'word' in item:
                        words_from_reco.append(item['word'])

        all_words: Set[str] = set(words_from_db) | set(words_from_reco)
        session.close()
        return list(all_words)

    async def _get_user_practiced_words(
            self,
            user_idx: int,
            limit: int = 200
    ) -> List[str]:
        session: Session = self.db.get_session()

        stmt = (
            select(distinct(Word.text))
            .join(PracticeWord, PracticeWord.word_idx == Word.word_idx)
            .join(PracticeSession, PracticeSession.session_idx == PracticeWord.session_idx)
            .where(
                PracticeSession.user_idx == user_idx,
                PracticeWord.word_idx.is_not(None)
            )
            .order_by(PracticeSession.created_at.desc())
            .limit(limit)
        )
        session.close()
        return list(session.scalars(stmt).all())

    async def get_highest_cleared_stage(self, user_idx: int) -> int:
        session: Session = self.db.get_session()

        stmt = (
            select(func.max(UserStageProgress.stage_id))
            .where(
                UserStageProgress.user_idx == user_idx,
                UserStageProgress.cleared == 1
            )
        )

        highest: int | None = session.scalar(stmt)
        session.close()
        print(highest)
        return highest or 0

    async def get_all_stages_data(self) -> list[StageData]:
        session: Session = self.db.get_session()
        stmt = select(StageWords)
        rows = session.scalars(stmt).all()
        session.close()
        return [
            StageData(
                id=row.stage_id,
                level=row.level,
                difficulty=row.difficulty,
                goalValue=row.goal_value,
                speed=row.speed,
                interval=row.interval_ms,
                lives=row.lives,
                words=row.words,
            )
            for row in rows
        ]

    async def save_clear_stage(self, user_idx: int, stage_id: int) -> None:
        session: Session = self.db.get_session()

        progress: UserStageProgress | None = session.get(
            UserStageProgress, (user_idx, stage_id)
        )

        if progress is not None:
            return

        session.add(
            UserStageProgress(
                user_idx=user_idx,
                stage_id=stage_id,
                cleared=1,
                cleared_at=datetime.utcnow(),
            )
        )
        session.commit()
        session.close()

    async def save_endless_best_score(self, user_idx: int, new_score: int) -> None:
        session: Session = self.db.get_session()
        try:
            stmt = insert(EndlessScores).values(
                user_idx=user_idx,
                best_score=new_score,
                updated_at=datetime.utcnow()
            )
            update_dict = {
                "best_score": stmt.inserted.best_score,
                "updated_at": datetime.utcnow(),
            }
            stmt = stmt.on_duplicate_key_update(**update_dict)

            session.execute(stmt)
            session.commit()
        except Exception as e:
            session.rollback()
            raise CustomException(
                status_code=500,
                detail="무한 도전 모드 점수 저장 중 오류가 발생했습니다."
            )  # or raise CustomException(...) 등으로 감싸기
        finally:
            session.close()

    async def get_best_score(self, user_idx: int) -> int:
        session: Session = self.db.get_session()
        stmt = (
            select(func.max(EndlessScores.best_score))
            .where(
                EndlessScores.user_idx == user_idx,
            )
        )

        best_score: int | None = session.scalar(stmt)
        session.close()
        return best_score or 0
