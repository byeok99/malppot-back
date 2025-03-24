from fastapi import APIRouter, UploadFile, File, Form
from .service import PronunciationService
from .schema import PronunciationAssessmentResponse
import tempfile

router = APIRouter(prefix="/api/pronunciation", tags=["Pronunciation Assessment"])

pronunciation_service = PronunciationService()

@router.post("/evaluate", response_model=PronunciationAssessmentResponse)
async def evaluate_pronunciation(
    file: UploadFile = File(...),
    reference_text: str = Form(...)
):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    result = pronunciation_service.assess_pronunciation(tmp_path, reference_text)
    return result