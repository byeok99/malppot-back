import logging

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from malppot.common.dependencies import get_current_user
from malppot.common.di_providers import (
    get_mypage_service_from_di
)
from malppot.common.errors import UserNotFoundException
from malppot.domain.models import User
from malppot.domain.mypage.schema import (
    MyPageResponse,
    SummaryResponse,
    PhonemeDetailResponse,
    PatientReport
)
from malppot.domain.mypage.service import MyPageService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/data", response_model=MyPageResponse)
async def get_mypage_data(
        user: User = Depends(get_current_user),
        mypage_service: MyPageService = Depends(get_mypage_service_from_di)
) -> MyPageResponse:
    try:
        data = await mypage_service.get_mypage_data(user.user_idx)
        return data
    except UserNotFoundException as e:
        logger.error(f"User not found via AuthService: {e.detail}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )
    except Exception as e:
        logger.exception(f"Unexpected error during user lookup for WebSocket: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


# malppot/domain/mypage/controller.py
@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
        user: User = Depends(get_current_user),
        svc: MyPageService = Depends(get_mypage_service_from_di),
):
    return await svc.get_summary(user.user_idx)


@router.get("/phoneme/{jamo}", response_model=PhonemeDetailResponse)
async def get_phoneme_detail(
        jamo: str,
        user: User = Depends(get_current_user),
        svc: MyPageService = Depends(get_mypage_service_from_di),
):
    return await svc.get_phoneme_detail(user.user_idx, jamo)


@router.get("/report", response_model=PatientReport)
async def get_phoneme(
        user: User = Depends(get_current_user),
        svc: MyPageService = Depends(get_mypage_service_from_di),
):
    return svc.get_report(user.user_idx)
