from pydantic import BaseModel
from typing import List

class ConvertResponse(BaseModel):
    converted_text: str

class ConvertRequest(BaseModel):
    input_text: str
    
class PronunciationIdResponse(BaseModel):
    pronunciation_id: str

class PhonemeScore(BaseModel):
    phoneme: str
    score: float

class PronunciationAssessmentResponse(BaseModel):
    reference_text: str
    recognized_text: str
    accuracy_score: float
    fluency_score: float
    completeness_score: float
    phoneme_scores: List[PhonemeScore]
