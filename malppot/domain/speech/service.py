import azure.cognitiveservices.speech as speechsdk
from malppot.conf.settings import AzureSpeechConfig
from malppot.domain.speech.G2P.KoG2Padvanced import KoG2Padvanced
from malppot.domain.speech.feedback.comp import map_jamos_with_scores, prepare_interpolation_jobs_from_scores
from sqlalchemy import text
from collections import defaultdict
import uuid
from azure.cognitiveservices.speech import (
    SpeechConfig, AudioConfig, SpeechRecognizer,
    PronunciationAssessmentConfig, PronunciationAssessmentGradingSystem,
    PronunciationAssessmentGranularity, PropertyId, PronunciationAssessmentResult
)
import json
import datetime
from fastapi import HTTPException
import os
import replicate
import requests


class SpeechService:
    def __init__(self, config: AzureSpeechConfig, db):
        if isinstance(config, dict):
            config = AzureSpeechConfig(**config)
        self.config = config
        self.db = db
        
    def interpolate_and_save(self, frame1_url: str, frame2_url: str, output_dir="static", output_filename="output.mp4"):
        # Replicate API 토큰 코드 상에서 직접 설정
        os.environ["REPLICATE_API_TOKEN"] = self.config.replicate_key;

        # 환경변수에서 자동 인식
        client = replicate.Client()

        # 입력 구성
        input_data = {
            "frame1": frame1_url,
            "frame2": frame2_url,
            "times_to_interpolate": 7
        }
        try:
            output_url = client.run(
                "google-research/frame-interpolation:4f88a16a13673a8b589c18866e540556170a5bcb2ccdc12de556e800e9456d3d",
                input=input_data
            )
        except Exception as e:
            print(f"Replicate 오류: {e}")
            return None

        # static 디렉토리 만들기
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_filename)

        res = requests.get(output_url)
        if res.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(res.content)
            print(f"저장 완료: {output_path}")
            return output_path
        else:
            print(f"다운로드 실패: {res.status_code}")
            return None
    
    def evaluate_pronunciation(self, reference_text: str, audio_path: str):
        speech_config = speechsdk.SpeechConfig(
            subscription=self.config.azure_key,
            region=self.config.azure_region
        )
        speech_config.speech_recognition_language = "ko-KR"
        audio_config = speechsdk.AudioConfig(filename=audio_path)

        pronunciation_config = speechsdk.PronunciationAssessmentConfig(
            reference_text=reference_text,
            grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
            granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
            enable_miscue=True
        )
        pronunciation_config.enable_prosody_assessment()

        recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        pronunciation_config.apply_to(recognizer)

        result = recognizer.recognize_once()
        if result.reason == speechsdk.ResultReason.Canceled:
            cancellation = speechsdk.CancellationDetails(result)
            raise Exception(f"Speech canceled: {cancellation.reason}, {cancellation.error_details}")

        json_str = result.properties.get(PropertyId.SpeechServiceResponse_JsonResult)
        parsed = json.loads(json_str)
        print(parsed)

        assessment_result = speechsdk.PronunciationAssessmentResult(result)

        word_phoneme_scores = []  # 순서 보존용 리스트
        phoneme_scores = []

        try:

            words = parsed["NBest"][0]["Words"]
            for word in words:
                word_text = word.get("Word", "")
                phonemes = word.get("Phonemes", [])
                errtype = word.get("PronunciationAssessment", {}).get("ErrorType", "None")
            
                scores = []
                for p in phonemes:
                    score = p.get("PronunciationAssessment", {}).get("AccuracyScore")
                    if score is not None:
                        scores.append(score)
            
                word_phoneme_scores.append((word_text, scores, errtype))

        except Exception as e:
            print(f"파싱 에러: {e}")
            phoneme_scores = []

        # feedback = map_jamos_with_scores(word_phoneme_scores)
        feedback = map_jamos_with_scores(word_phoneme_scores)

        # 영상 생성 job 준비
        jobs = prepare_interpolation_jobs_from_scores(feedback)

        # 생성된 영상 경로 저장
        video_results = []
        for job in jobs:
            # 이 부분에서 이미 있는 데이터가 있으면 self.interpolate_and_save 호출 안 하게 하고 output_path 이름만
            output_path = self.interpolate_and_save(
                frame1_url=job["frame1"],
                frame2_url=job["frame2"],
                output_filename=job["output"]
            )
            if output_path:
                video_results.append(output_path)

        # 평균 점수 계산 추가
        for f in feedback:
            scores = [s["score"] for s in f["scores"] if "score" in s]
            f["average_score"] = round(sum(scores) / len(scores), 2) if scores else 0.0

        # 최종 반환 구조
        return {
            "reference_text": reference_text,
            "accuracy_score": assessment_result.accuracy_score,
            "fluency_score": assessment_result.fluency_score,
            "completeness_score": assessment_result.completeness_score,
            "phoneme_scores": phoneme_scores,
            "feedback": feedback,
            "videos": video_results
        }

    def save_pronunciation_log(self, user_id: int, result: dict) -> str:
        pronunciation_id = str(uuid.uuid4())  # UUID로 고유 ID 생성

        session = self.db.get_session()
        try:
            session.execute(
                text("""
                INSERT INTO pronunciation_logs (
                    pronunciation_id,
                    user_id,
                    reference_text,
                    accuracy_score,
                    fluency_score,
                    completeness_score,
                    phoneme_scores,
                    feedback,
                    created_at
                ) VALUES (
                    :pronunciation_id,
                    :user_id,
                    :reference_text,
                    :accuracy_score,
                    :fluency_score,
                    :completeness_score,
                    :phoneme_scores,
                    :feedback,
                    :created_at
                )
                """),
                {
                    "pronunciation_id": pronunciation_id,
                    "user_id": user_id,
                    "reference_text": result["reference_text"],
                    "accuracy_score": result["accuracy_score"],
                    "fluency_score": result["fluency_score"],
                    "completeness_score": result["completeness_score"],
                    "phoneme_scores": json.dumps(result["phoneme_scores"]),
                    "feedback": json.dumps(result["feedback"]),
                    "created_at": datetime.datetime.utcnow(),
                }
            )
            session.commit()
        finally:
            session.close()

        return pronunciation_id
    
    def get_pronunciation_result_by_id(self, pronunciation_id: str, user_id: int) -> dict:
        session = self.db.get_session()
        try:
            result = session.execute(
                text("""
                    SELECT pronunciation_id, reference_text, accuracy_score, 
                    fluency_score, completeness_score, feedback, created_at
                    FROM pronunciation_logs
                    WHERE pronunciation_id = :pronunciation_id AND user_id = :user_id
                """),
                {
                    "pronunciation_id": pronunciation_id,
                    "user_id": user_id
                }
            )
            row = result.mappings().fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="해당 발음 결과가 없거나 권한이 없습니다.")
    
            result_dict = dict(row)
            #if isinstance(result_dict.get("phoneme_scores"), str):
            #    result_dict["phoneme_scores"] = json.loads(result_dict["phoneme_scores"])
            if isinstance(result_dict.get("feedback"), str):
                result_dict["feedback"] = json.loads(result_dict["feedback"])

            return result_dict
        finally:
            session.close()
        
    def convert_pronunciation(self, input_text: str):
        result = KoG2Padvanced(input_text)
        return result
