from pydantic import BaseModel

class PronunciationAssessmentResponse(BaseModel):
    recognized_text: str
    accuracy_score: float
    pronunciation_score: float
    fluency_score: float
    completeness_score: float