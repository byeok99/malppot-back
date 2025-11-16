from typing import List, Optional

from pydantic import BaseModel, Field


class ConvertResponse(BaseModel):
    converted_text: str


class ConvertRequest(BaseModel):
    input_text: str


class PhonemeScore(BaseModel):
    phoneme: str
    score: float


class SyllableDetail(BaseModel):
    char: str
    tongueUrl: Optional[str] = None  # 혀 모양 GIF 이미지 URL
    lipsUrl: Optional[str] = None
    score: Optional[float] = None
    gptTip: Optional[str] = None


class WordFeedback(BaseModel):
    word: str
    score: float
    videoUrl: Optional[str] = None  # HeyGen 영상 URL
    syllables: List[SyllableDetail]
    errtype: Optional[str] = None  # Azure에서 제공하는 오류 유형 (예: Mispronunciation, Omission 등)


class EvaluationResponse(BaseModel):
    session_id: str  # 세션 ID 추가
    sentence: str = Field(..., alias="reference_text")  # 전체 문장
    totalScore: float = Field(..., alias="accuracy_score")  # 전체 정확도 점수
    fluencyScore: float = Field(..., alias="fluency_score")  # 유창성 점수
    completenessScore: float = Field(..., alias="completeness_score")  # 완전성 점수
    wordFeedbacks: List[WordFeedback]


class SyllableDetailResponse(BaseModel):
    char: str
    tongue_url: Optional[List[str]]
    lips_url: Optional[List[str]]
    gpt_tip: Optional[str] = ""
