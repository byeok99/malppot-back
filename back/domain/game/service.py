from typing import List, Tuple

from sqlalchemy import select, func
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session, joinedload

from malppot.common.errors import CustomException
from malppot.common.gpt_service import GPTService
from malppot.domain.game.schema import StageData
from malppot.domain.models import (
    UserStageProgress,
    EndlessScores,
    StageInfo,
    GameWord
)
from malppot.utils.datetime_utils import now_kst


class GameService:
    def __init__(self, db, gpt_service: GPTService):
        self.db = db
        self.gpt_service = gpt_service

    async def get_endless_word_pool(self) -> List[Tuple[str, str]]:
        session: Session = self.db.get_session()

        stmt_reco = select(GameWord.word, GameWord.image_url)
        result = session.execute(stmt_reco)
        reco_rows = result.all()
        tuple_rows = [tuple(row) for row in reco_rows]
        session.close()

        return tuple_rows

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
        return highest or 0

    async def get_all_stages_data(self) -> list[StageData]:
        session: Session = self.db.get_session()
        stmt = select(StageInfo).options(joinedload(StageInfo.words))
        rows = session.scalars(stmt).unique().all()
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
                words=[
                    {"word": gw.word, "image_url": gw.image_url}
                    for gw in row.words
                ],
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
                cleared_at=now_kst(),
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
                updated_at=now_kst()
            )
            update_dict = {
                "best_score": stmt.inserted.best_score,
                "updated_at": now_kst(),
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
