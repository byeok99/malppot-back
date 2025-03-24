import azure.cognitiveservices.speech as speechsdk
from ..settings import azure_settings

class PronunciationService:
    def __init__(self):
        self.azure_key = azure_settings.azure_key
        self.azure_region = azure_settings.azure_region

    def assess_pronunciation(self, audio_file_path: str, reference_text: str):
        speech_config = speechsdk.SpeechConfig(subscription=self.azure_key, region=self.azure_region)
        audio_input = speechsdk.audio.AudioConfig(filename=audio_file_path)

        assessment_config = speechsdk.PronunciationAssessmentConfig(
            reference_text=reference_text,
            grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
            granularity=speechsdk.PronunciationAssessmentGranularity.Word,
            dimension=speechsdk.PronunciationAssessmentDimension.Comprehensive
        )

        recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)
        assessment_config.apply_to(recognizer)

        result = recognizer.recognize_once()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            pa_result = speechsdk.PronunciationAssessmentResult(result)
            return {
                "recognized_text": result.text,
                "accuracy_score": pa_result.accuracy_score,
                "pronunciation_score": pa_result.pronunciation_score,
                "fluency_score": pa_result.fluency_score,
                "completeness_score": pa_result.completeness_score
            }
        else:
            return {"error": f"Recognition failed: {result.reason}"}