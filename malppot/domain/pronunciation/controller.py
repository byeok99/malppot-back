from fastapi import APIRouter, UploadFile, File, Form, Depends, Request, HTTPException
from dependency_injector.wiring import inject, Provide
from .schema import PronunciationIdResponse, PronunciationConvertResponse, PronunciationConvertRequest, PronunciationAssessmentResponse
from malppot.di import DI
import tempfile
import shutil
import jwt

router = APIRouter()


@router.post("/convert", response_model=PronunciationConvertResponse)
@inject
async def con_pronunciation(
    request: PronunciationConvertRequest,
    pronunciation_service = Depends(Provide[DI.pronunciation.service]),
):
    result = pronunciation_service.convert_pronunciation(request.input_text)
    return PronunciationConvertResponse(converted_text=result)


@router.post("/evaluate", response_model=PronunciationIdResponse)
@inject
async def evaluate_pronunciation(
    request: Request,
    reference_text: str = Form(...),
    audio: UploadFile = File(...),
    pronunciation_service = Depends(Provide[DI.pronunciation.service]),
    jwt_service = Provide[DI.jwt_service],
    auth_service = Provide[DI.auth.service]
):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing")
    token = auth_header.replace("Bearer ", "").strip()
    if not token:
        print("No access token")
        return
    try:
        user_id = jwt_service.get_user_id(token)
        if not user_id:
            print("Invalid Token")
            return
    except jwt.ExpiredSignatureError:
        print("Token has expired")
        return
    
    try:
        user = auth_service.get_user_by_id(user_id)
    except HTTPException as e:
        print(f"User not found: {e.detail}")
        return
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        shutil.copyfileobj(audio.file, tmp)
        tmp_path = tmp.name

    pronunciation_result = pronunciation_service.evaluate_pronunciation(reference_text, tmp_path)
    pronunciation_id = pronunciation_service.save_pronunciation_log(user_id=user.user_idx, result=pronunciation_result)
    return PronunciationIdResponse(pronunciation_id=pronunciation_id)
        
@router.get("/evaluate/result/{pronunciation_id}")
@inject
async def get_pronunciation_result_by_id(
    request: Request,
    pronunciation_id: str,
    pronunciation_service = Depends(Provide[DI.pronunciation.service]),
    jwt_service = Provide[DI.jwt_service],
    auth_service = Provide[DI.auth.service]
):
    # 인증
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing")
    token = auth_header.replace("Bearer ", "").strip()
    if not token:
        print("No access token")
        return
    try:
        user_id = jwt_service.get_user_id(token)
        if not user_id:
            print("Invalid Token")
            return
    except jwt.ExpiredSignatureError:
        print("Token has expired")
        return
    
    try:
        user = auth_service.get_user_by_id(user_id)
    except HTTPException as e:
        print(f"User not found: {e.detail}")
        return

    result = pronunciation_service.get_pronunciation_result_by_id(pronunciation_id, user_id=user.user_idx)

    return result