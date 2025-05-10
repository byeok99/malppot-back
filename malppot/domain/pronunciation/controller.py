from fastapi import APIRouter, UploadFile, File, Form, Depends, Request, HTTPException
from starlette.responses import FileResponse
from dependency_injector.wiring import inject, Provide
from .schema import PronunciationIdResponse, PronunciationConvertResponse, PronunciationConvertRequest, PronunciationAssessmentResponse
from malppot.di import DI
from pydub import AudioSegment
import tempfile, shutil, jwt, os

router = APIRouter()


@router.post("/convert", response_model=PronunciationConvertResponse)
@inject
async def con_pronunciation(
    request: PronunciationConvertRequest,
    pronunciation_service = Depends(Provide[DI.pronunciation.service]),
):
    result = pronunciation_service.convert_pronunciation(request.input_text)
    return PronunciationConvertResponse(converted_text=result)


@router.post("/evaluate")
@inject
async def evaluate_pronunciation(
    request: Request,
    reference_text: str = Form(...),
    audio: UploadFile = File(...),
    pronunciation_service = Provide[DI.pronunciation.service],
    jwt_service = Provide[DI.jwt_service],
    auth_service = Provide[DI.auth.service]
):
    auth_header = request.headers.get("Authorization")
    token = auth_header.replace("Bearer ", "").strip() if auth_header else None
    user_id = jwt_service.get_user_id(token)
    user = auth_service.get_user_by_id(user_id)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_webm:
        shutil.copyfileobj(audio.file, temp_webm)
        webm_path = temp_webm.name

    wav_path = webm_path.replace(".webm", ".wav")
    try:
        sound = AudioSegment.from_file(webm_path, format="webm")
        sound = sound.set_channels(1).set_frame_rate(16000)
        sound.export(wav_path, format="wav")
    except Exception as e:
        print(f"Audio conversion failed: {e}")
        raise HTTPException(status_code=500, detail="Audio conversion failed")

    pronunciation_result = pronunciation_service.evaluate_pronunciation(reference_text, wav_path)
    pronunciation_service.save_pronunciation_log(user_id=user.user_idx, result=pronunciation_result)

    os.remove(webm_path)
    os.remove(wav_path)

    return pronunciation_result

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
