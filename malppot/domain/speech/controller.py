import logging
import os

from fastapi import APIRouter, Depends, UploadFile, File, Form, status

from malppot.common.dependencies import get_current_user
from malppot.common.di_providers import get_speech_service_from_di
from malppot.common.errors import (
    SpeechEvaluationException,
    SpeechAudioProcessingException,
    CustomException,
    UserNotFoundException
)
from malppot.domain.models import User
from malppot.domain.speech.schema import ConvertResponse, ConvertRequest, SyllableDetailResponse
from malppot.domain.speech.service import SpeechService
from malppot.utils.audio_utils import convert_upload_to_wav

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/convert", response_model=ConvertResponse)
async def convert(
        request_data: ConvertRequest,
        speech_service: SpeechService = Depends(get_speech_service_from_di),
):
    try:
        result = await speech_service.convert(request_data.input_text)
        return ConvertResponse(converted_text=result['converted_text'])
    except Exception as e:
        logger.exception("An unexpected error occurred during text conversion.")
        raise CustomException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during text conversion."
        )


@router.post("/evaluate")
async def evaluate(
        reference_text: str = Form(...),
        original_text: str = Form(...),
        audio: UploadFile = File(...),
        speech_service: SpeechService = Depends(get_speech_service_from_di),
        user: User = Depends(get_current_user)
):
    wav_path = None

    try:
        logger.info(f"Received evaluation request for reference: {reference_text[:50]}...")

        if not audio.filename:
            raise SpeechAudioProcessingException(detail="Audio file name is missing.")
        if not audio.file:
            raise SpeechAudioProcessingException(detail="Audio file content is missing.")

        wav_path = await convert_upload_to_wav(audio)
        result = await speech_service.evaluate(original_text, reference_text, wav_path)
        session_id = speech_service.save_to_practice_tables(user.user_idx, original_text, result)
        speech_service.update_user_practice_summary(user.user_idx)
        return {
            "session_id": session_id,
            "reference_text": original_text,
            "scores": result["accuracy_score"],
            "feedback": result["word_feedbacks"],
        }
    except SpeechAudioProcessingException as e:
        logger.error(f"Audio processing error during evaluate: {e.detail}")
        raise e
    except SpeechEvaluationException as e:
        logger.error(f"Speech evaluation failed by service: {e.detail}")
        raise e
    except UserNotFoundException as e:
        logger.error(f"User not found during evaluation: {e.detail}")
        raise e
    except Exception as e:
        logger.exception("An unexpected error occurred during speech evaluation process.")
        raise CustomException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during speech evaluation process."
        )
    finally:
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)
            logger.info(f"Cleaned up temporary WAV file: {wav_path}")


@router.get("/syllable/{char}", response_model=SyllableDetailResponse)
async def get_syllable_detail(
        char: str,
        speech_service: SpeechService = Depends(get_speech_service_from_di)
):
    """
    한글 음절(char)에 대한 입모양, 혀모양, gpt_tip 정보를 조회
    """
    result = speech_service.get_syllable_detail(char)
    return SyllableDetailResponse(**result)
