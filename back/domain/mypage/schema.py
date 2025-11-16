from datetime import date
from typing import List, Dict, Optional, Literal

from pydantic import BaseModel, Field


# 1. UserData 스키마 (사용자 요약 정보)
class Accuracy(BaseModel):
    previous: float
    current: float


class MyPageUserData(BaseModel):
    userName: str = Field(..., description="사용자 이름")
    profileImageUrl: Optional[str] = Field(None, description="사용자 프로필 이미지 URL")
    practiceStreak: int = Field(..., description="연속 연습일")
    totalPracticeCount: int = Field(..., description="총 연습 횟수")
    accuracy: Accuracy = Field(..., description="평균 정확도 변화")


# 2. GraphData 스키마 (주간 정확도 변화 그래프 데이터 포인트)
class MyPageGraphDataPoint(BaseModel):
    # 👇 [수정] 필드 이름을 'date'에서 'record_date'로 변경
    record_date: date = Field(..., description="날짜 (YYYY-MM-DD)")
    score: float = Field(..., description="해당 날짜의 정확도 점수")


# 3. PhonemeAccuracy 스키마 (자음별/된소리별 정확도)
# 파이썬 딕셔너리 타입을 직접 사용 (Pydantic은 기본적으로 Dict[str, float] 지원)

# 4. DetailedAnalysisItem 스키마 (단어별 분석 리포트 항목)
class MyPageDetailedAnalysisItem(BaseModel):
    id: str = Field(..., description="단어별 분석 항목 고유 ID (practice_word_idx)")
    word: str = Field(..., description="연습 단어 텍스트")
    phoneme: str = Field(..., description="단어의 주요 자음 (분석 기준 자음)")
    accuracy: float = Field(..., description="단어의 정확도 점수")
    mainErrorType: str = Field(..., description="주요 오류 유형 (Omission, Insertion 등)")
    history: List[float] = Field(..., description="단어의 과거 정확도 점수 변화 추이")


# 5. ComprehensiveData 스키마 (종합 분석)
class MyPageErrorDistribution(BaseModel):
    Omission: int = Field(..., alias="Omission")
    Insertion: int = Field(..., alias="Insertion")
    Mispronunciation: int = Field(..., alias="Mispronunciation")
    None_: Optional[int] = Field(None, alias="None")


# MyPageComprehensiveData를 MyPageErrorDistribution 위에 정의해야 함 (의존성 때문)
class MyPageComprehensiveData(BaseModel):
    errorDistribution: MyPageErrorDistribution
    soundCategoryAccuracy: Dict[str, float] = Field(..., description="소리 계열별 평균 정확도")


class ErrorTendency(BaseModel):
    # replacement: int = Field(0, alias="대치")  # %
    distortion: int = Field(0, alias="왜곡")  # %
    omission: int = Field(0, alias="생략")  # %
    insertion: int = Field(0, alias="첨가")  # %
    none: int = Field(0, alias="없음")


class PhonemePositionAnalysis(BaseModel):
    averageAccuracy: float  # 위치별 평균 정확도
    errorTendency: ErrorTendency


class PhonemeAnalysis(BaseModel):
    overallAccuracy: float
    positionalAnalysis: Dict[str, Optional[PhonemePositionAnalysis]]  # initial/final …
    recommendedWords: List[dict[str, str]]
    allRecords: List[MyPageDetailedAnalysisItem]


# 6. 마이페이지 전체 응답 스키마
class MyPageResponse(BaseModel):
    userData: MyPageUserData = Field(..., description="사용자 요약 정보")
    graphData: List[MyPageGraphDataPoint] = Field(..., description="주간 정확도 변화 그래프 데이터")
    phonemeAccuracy: Dict[str, float] = Field(..., description="자음별 평균 정확도")
    tenseConsonants: Dict[str, float] = Field(..., description="된소리/거센소리 자음별 평균 정확도")
    detailedAnalysis: List[MyPageDetailedAnalysisItem] = Field(..., description="단어별 상세 분석 리포트")
    comprehensiveData: MyPageComprehensiveData = Field(..., description="종합 분석 데이터")
    phonemeDetailedAnalysis: Dict[str, PhonemeAnalysis] = Field(..., description="자음별 상세 분석")


class SummaryResponse(BaseModel):
    userData: MyPageUserData
    graphData: list[MyPageGraphDataPoint]
    phonemeAccuracy: dict[str, float]  # ㄱㄴㄷ…
    tenseConsonants: dict[str, float]  # ㄲㄸ…


class PhonemeDetailResponse(BaseModel):
    phoneme: str  # 요청한 자음
    detail: PhonemeAnalysis


class ErrorTypeStat(BaseModel):
    error_type: Optional[str]
    count: int
    percent: float


class JamoDetail(BaseModel):
    phoneme: str  # 자음
    position: Literal["초성", "종성"]
    average_score: Optional[float]
    total_attempts: int
    error_types: List[ErrorTypeStat]


class PatientReport(BaseModel):
    name: str
    total_practice_count: int
    practice_streak: int
    overall_accuracy: float
    consonant_scores: Dict[str, float]  # 자음별 평균 정확도
    seven_day_accuracy_trend: List[float]
    attention_phonemes: List[Dict[str, float | str]]  # [{phoneme, position, accuracy}]
    jamo_detail: List[JamoDetail]
