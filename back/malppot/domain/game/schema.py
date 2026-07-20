import enum

from pydantic import BaseModel, condecimal


class Difficulty(str, enum.Enum):
    EASY = "EASY"
    NORMAL = "NORMAL"
    HARD = "HARD"


class StageData(BaseModel):
    id: int
    level: int
    difficulty: Difficulty
    goalValue: int
    speed: condecimal(max_digits=3, decimal_places=1)  # 0.0 ~ 9.9
    interval: int
    lives: int
    words: list[dict[str, str]]


class SaveBestScoreRequest(BaseModel):
    new_score: int


class StageClearReq(BaseModel):
    stage_id: int
