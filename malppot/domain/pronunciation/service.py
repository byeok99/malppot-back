import azure.cognitiveservices.speech as speechsdk
from malppot.conf.settings import AzureSpeechConfig
from malppot.domain.pronunciation.G2P.KoG2Padvanced import KoG2Padvanced
from malppot.domain.pronunciation.feedback.comp import map_jamos_with_scores
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


class PronunciationService:
    def __init__(self, config: AzureSpeechConfig, db):
        if isinstance(config, dict):
            config = AzureSpeechConfig(**config)
        self.config = config
        self.db = db

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

        feedback = map_jamos_with_scores(word_phoneme_scores)

        # 평균 점수 계산 추가
        for f in feedback:
            scores = [s["score"] for s in f["scores"] if "score" in s]
            f["average_score"] = round(sum(scores) / len(scores), 2) if scores else 0.0

        return {
            "reference_text": reference_text,
            "accuracy_score": assessment_result.accuracy_score,
            "fluency_score": assessment_result.fluency_score,
            "completeness_score": assessment_result.completeness_score,
            "phoneme_scores": phoneme_scores,
            "feedback": feedback
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
