from fastapi import APIRouter, UploadFile, File, Form
from dependency_injector.wiring import Provide
from .schema import PronunciationAssessmentResponse
import tempfile
from malppot.di import DI

router = APIRouter()


@router.post("/evaluate", response_model=PronunciationAssessmentResponse)
async def evaluate_pronunciation(
    file: UploadFile = File(...),
    reference_text: str = Form(...),
    pronunciation_service = Provide[DI.pronunciation.service],
):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    result = pronunciation_service.assess_pronunciation(tmp_path, reference_text)
    return result