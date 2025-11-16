import logging
import os

from fastapi import APIRouter, Depends, UploadFile, File, Form

from malppot.common.dependencies import get_current_user
from malppot.common.di_providers import (
    get_game_service_from_di,
    get_recommendation_service_from_di,
    get_speech_service_from_di,
)
from malppot.common.errors import (
    CustomException
)
from malppot.domain.game.schema import SaveBestScoreRequest, StageClearReq
from malppot.domain.game.service import GameService
from malppot.domain.models import User
from malppot.domain.recommendation.service import RecommendationService
from malppot.domain.speech.service import SpeechService
from malppot.utils.audio_utils import convert_upload_to_wav

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/test/{jamo}")
async def test(
        jamo: str,
        recommendation_service: RecommendationService = Depends(get_recommendation_service_from_di),
):
    await recommendation_service.save_recommendation_words(
        # ['ㄱ', 'ㄴ', 'ㄷ', 'ㄹ', 'ㅁ', 'ㅂ', '', 'ㅅ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ', 'ㄲ', 'ㄸ', 'ㅃ', 'ㅆ', 'ㅉ', ]
        # ['ㄲ', 'ㄸ', 'ㅃ', 'ㅆ', 'ㅉ']
        jamo
    )


@router.post("/words")
async def word_pool(
        game_service: GameService = Depends(get_game_service_from_di)
):
    words = await game_service.get_endless_word_pool()
    return {"words": words}


@router.get("/highest-cleared")
async def get_highest_cleared_stage(
        game_service: GameService = Depends(get_game_service_from_di),
        user: User = Depends(get_current_user)
):
    highest_stage = await game_service.get_highest_cleared_stage(user.user_idx)
    return {"highest_stage": highest_stage}


@router.get("/stages")
async def get_all_stages(
        game_service: GameService = Depends(get_game_service_from_di),
):
    data = await game_service.get_all_stages_data()
    return data


@router.post("/clear")
async def save_clear_stage(
        req: StageClearReq,
        game_service: GameService = Depends(get_game_service_from_di),
        user: User = Depends(get_current_user)
) -> None:
    try:
        await game_service.save_clear_stage(user.user_idx, req.stage_id)
    except CustomException as e:
        logger.exception("[mark-cleared] unexpected error")
        raise CustomException(status_code=500, detail="스테이지 클리어 기록 저장 중 오류가 발생했습니다.")


@router.post("/endless")
async def save_best_score(
        request: SaveBestScoreRequest,
        game_service: GameService = Depends(get_game_service_from_di),
        user: User = Depends(get_current_user),
) -> None:
    try:
        await game_service.save_endless_best_score(user.user_idx, request.new_score)
    except CustomException as e:
        logger.exception("[save-best-score] unexpected error")
        raise CustomException(status_code=500, detail="무한 도전 모드 점수 갱신에 실패했습니다.")


@router.get("/best-score")
async def get_best_score(
        game_service: GameService = Depends(get_game_service_from_di),
        user: User = Depends(get_current_user),
) -> int:
    try:
        return await game_service.get_best_score(user.user_idx)

    except CustomException as e:
        logger.exception("[get-best-score] unexpected error")
        raise CustomException(status_code=500, detail="최고 기록을 가져오는데 실패했습니다.")


@router.post("/evaluate/bulk")
async def evaluate_bulk(
        reference_text: str = Form(...),  # 예: "고릴라 구구 비둘기 …"
        original_text: str = Form(...),  # 예: "고릴라 비둘기"
        audio: UploadFile = File(...),
        speech_service: SpeechService = Depends(get_speech_service_from_di),
        user: User = Depends(get_current_user),
):
    wav_path: str | None = None
    try:
        # 1. 파일 → wav
        wav_path = await convert_upload_to_wav(audio)

        # 2. Azure 평가 수행
        result = await speech_service.evaluate(
            original_text=original_text,
            reference_text=reference_text,
            audio_path=wav_path,
        )

        # 3. **original_text 기준으로만 저장**
        matched_words = set(original_text.split())
        session_id = speech_service.save_practice_filtered(
            user_idx=user.user_idx,
            original_text=original_text,
            result=result,
            matched_words=matched_words,
        )
        speech_service.update_user_practice_summary(user.user_idx)

        return {
            "session_id": session_id,
            "reference_text": reference_text,
            "original_text": original_text,
            "scores": result["accuracy_score"],
            "feedback": result["word_feedbacks"],
        }
    except Exception as e:
        logger.exception("[bulk-evaluate] unexpected error")
        raise CustomException(status_code=500, detail="Bulk evaluation failed")
    finally:
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)
