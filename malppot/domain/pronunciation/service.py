import azure.cognitiveservices.speech as speechsdk
from malppot.conf.settings import AzureSpeechConfig
from malppot.domain.pronunciation.G2P.KoG2Padvanced import KoG2Padvanced
from sqlalchemy import text
import uuid
from azure.cognitiveservices.speech import (
    SpeechConfig, AudioConfig, SpeechRecognizer,
    PronunciationAssessmentConfig, PronunciationAssessmentGradingSystem,
    PronunciationAssessmentGranularity, PropertyId, PronunciationAssessmentResult
)
import json
import datetime
from collections import defaultdict
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

        # 발음 평가 설정
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

        recognized_text = result.text or ""
        assessment_result = speechsdk.PronunciationAssessmentResult(result)

        json_str = result.properties.get(PropertyId.SpeechServiceResponse_JsonResult)
        parsed = json.loads(json_str)
        print(parsed)

        phoneme_scores = []

        try:
            words = parsed["NBest"][0]["Words"]
            for word in words:
                word_text = word.get("Word", "")
                phonemes = word.get("Phonemes", [])
                for p in phonemes:
                    phoneme_scores.append({
                        "word": word_text,
                        "phoneme": p.get("Phoneme", ""),  # 여기에 phoneme이 들어가게 됨
                        "score": p.get("PronunciationAssessment", {}).get("AccuracyScore"),
                        "offset": p.get("Offset"),
                        "duration": p.get("Duration")
                    })
        except Exception as e:
            print(f"파싱 에러: {e}")
            pass

        return {
            "reference_text": reference_text,
            "recognized_text": recognized_text,
            "accuracy_score": assessment_result.accuracy_score,
            "fluency_score": assessment_result.fluency_score,
            "completeness_score": assessment_result.completeness_score,
            "phoneme_scores": phoneme_scores
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
                    recognized_text,
                    accuracy_score,
                    fluency_score,
                    completeness_score,
                    phoneme_scores,
                    created_at
                ) VALUES (
                    :pronunciation_id,
                    :user_id,
                    :reference_text,
                    :recognized_text,
                    :accuracy_score,
                    :fluency_score,
                    :completeness_score,
                    :phoneme_scores,
                    :created_at
                )
                """),
                {
                    "pronunciation_id": pronunciation_id,
                    "user_id": user_id,
                    "reference_text": result["reference_text"],
                    "recognized_text": result["recognized_text"],
                    "accuracy_score": result["accuracy_score"],
                    "fluency_score": result["fluency_score"],
                    "completeness_score": result["completeness_score"],
                    "phoneme_scores": json.dumps(result["phoneme_scores"]),
                    "created_at": datetime.datetime.utcnow(),
                }
            )
            session.commit()
        finally:
            session.close()

        return pronunciation_id
    
    def get_pronunciation_result_by_id(self, pronunciation_id: str, user_id: int) -> dict:
        def group_by_word_sequence(phoneme_scores):
            word_sequence = []
            buffer = []
            prev_word = None

            for item in phoneme_scores:
                word = item["word"]
                score = item["score"]
                if not word:
                    continue

                if word != prev_word and buffer:
                    avg = round(sum(score for _, score in buffer) / len(buffer), 2)
                    word_sequence.append({
                        "word": buffer[0][0],
                        "avg_score": avg
                    })
                    buffer = []

                buffer.append((word, score))
                prev_word = word

            if buffer:
                avg = round(sum(score for _, score in buffer) / len(buffer), 2)
                word_sequence.append({
                    "word": buffer[0][0],
                    "avg_score": avg
                })

            return word_sequence

        session = self.db.get_session()
        try:
            result = session.execute(
                text("""
                    SELECT pronunciation_id, reference_text, recognized_text,
                           accuracy_score, fluency_score, completeness_score,
                           phoneme_scores, created_at
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
            raw_phoneme_scores = json.loads(result_dict["phoneme_scores"])
            result_dict["phoneme_scores"] = group_by_word_sequence(raw_phoneme_scores)
    
            return result_dict
        finally:
            session.close()
        
    def convert_pronunciation(self, input_text: str):
        result = KoG2Padvanced(input_text)
        return result
    