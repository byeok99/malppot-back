import asyncio
import datetime
import json
import os
from typing import Dict, List, Iterable
from uuid import uuid4

import azure.cognitiveservices.speech as speechsdk
import replicate
import requests
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from malppot.common.gpt_service import GPTService
from malppot.conf.settings import AzureSpeechConfig
from malppot.domain.heygen.service import HeyGenService
from malppot.domain.models import (
    User,
    PracticeSession,
    PracticeWord,
    PronunciationScore,
    JamoStatistic,
    Word,
    PracticeWordPosition,
    Syllable
)
from malppot.domain.speech.G2P.KoG2Padvanced import KoG2Padvanced
from malppot.domain.speech.feedback.comp import (
    map_jamos_with_scores,
    VISEME_TABLE,
    make_tongue_jobs_for_syllable,
    extract_lip_movement_sequence,
    make_lips_jobs_from_sequence
)
from malppot.utils.text_utils import extract_unique_syllables


class SpeechService:
    def __init__(self, config: AzureSpeechConfig, db, gpt_service: GPTService, heygen_service: HeyGenService):
        if isinstance(config, dict):
            config = AzureSpeechConfig(**config)
        self.config = config
        self.db = db
        self.gpt_service = gpt_service
        self.heygen_service = heygen_service

    async def convert(self, input_text: str):
        converted_text = KoG2Padvanced(input_text)
        unique_syllable = extract_unique_syllables(converted_text)

        asyncio.create_task(self._populate_syllable_tongue_videos(unique_syllable))

        lips_movement = extract_lip_movement_sequence(converted_text)
        asyncio.create_task(self._populate_syllable_lips_videos(lips_movement))

        return {"converted_text": converted_text}

    async def _populate_syllable_tongue_videos(self, syllable_chars: Iterable[str]) -> None:
        """
        syllable_chars: 음절 리스트 (예: ['학', '교', '에'])
        - DB에서 해당 음절의 tongue_url(=video_urls)이 없는 것만 선별해서
        - 글자 단위로 job 만들어서 영상 생성, DB 저장
        """
        session: Session = self.db.get_session()
        try:
            # 이미 DB에 등록된 syllable
            existing_rows = session.query(Syllable).filter(Syllable.syllable_char.in_(syllable_chars)).all()
            existing_map = {row.syllable_char: row for row in existing_rows}
            for ch in syllable_chars:
                syllable = existing_map.get(ch)
                urls = []
                if syllable and syllable.tongue_url:
                    try:
                        urls = json.loads(syllable.tongue_url)
                    except Exception:
                        urls = []
                # 이미 있으면 pass
                if urls:
                    continue

                # 1) job 생성 (초성/중성/종성에 따라 여러 조합)
                jobs = make_tongue_jobs_for_syllable(ch)
                # 2) 각 job마다 영상 생성 (이 부분은 await or run_in_executor)
                video_urls = []
                for job in jobs:
                    video_url = await self.make_single_video(job, 'tongue')
                    if video_url:
                        video_urls.append(str(video_url))

                # 3) DB 저장
                row = syllable or Syllable(syllable_char=ch)
                row.tongue_url = json.dumps(video_urls, ensure_ascii=False)
                if not syllable:
                    session.add(row)
            session.commit()
        finally:
            session.close()

    async def _populate_syllable_lips_videos(self, lips_movement: Iterable[dict]) -> None:
        session: Session = self.db.get_session()
        try:
            syllable_chars = [entry["letter"] for entry in lips_movement]
            existing_rows = session.query(Syllable).filter(Syllable.syllable_char.in_(syllable_chars)).all()
            existing_map = {row.syllable_char: row for row in existing_rows}
            for entry in lips_movement:
                ch = entry["letter"]
                seq = entry["sequence"]
                syllable = existing_map.get(ch)
                urls = []
                if syllable and syllable.lips_url:
                    try:
                        urls = json.loads(syllable.lips_url)
                    except Exception:
                        urls = []
                if urls:
                    continue

                jobs = make_lips_jobs_from_sequence(seq)
                video_urls = []
                for job in jobs:
                    if job['segment'] == '단독':
                        video_url = job['frame1']
                    else:
                        video_url = await self.make_single_video(job, 'lips')  # lips 영상도 같은 함수 사용

                    if video_url:
                        video_urls.append(str(video_url))

                row = syllable or Syllable(syllable_char=ch)
                row.lips_url = json.dumps(video_urls, ensure_ascii=False)
                if not syllable:
                    session.add(row)
            session.commit()
        finally:
            session.close()

    def get_filename_from_url(url: str):
        return os.path.basename(url).split("?")[0]

    async def make_single_video(self, job, save_path):
        os.environ["REPLICATE_API_TOKEN"] = self.config.replicate_key
        client = replicate.Client()

        if save_path == 'tongue':
            save_dir = os.path.join("malppot", "static", "tongue")
        else:
            save_dir = os.path.join("malppot", "static", "lips")

        os.makedirs(save_dir, exist_ok=True)

        # 파일명은 항상 "frame1_frame2.mp4"
        frame1_name = os.path.basename(job["frame1"])
        frame2_name = os.path.basename(job["frame2"])
        file_name = f"{frame1_name}_{frame2_name}.mp4"
        save_path = os.path.join(save_dir, file_name)

        # 이미 파일이 있으면 생성 생략!
        if os.path.exists(save_path):
            print(f"[이미존재] {save_path}")
            return f"/static/tongue/{file_name}"

        try:
            output_url = await asyncio.to_thread(
                lambda: client.run(
                    "google-research/frame-interpolation:4f88a16a13673a8b589c18866e540556170a5bcb2ccdc12de556e800e9456d3d",
                    input={
                        "frame1": job["frame1"],
                        "frame2": job["frame2"],
                        "times_to_interpolate": 7
                    }
                )
            )
            if isinstance(output_url, list):
                output_url = output_url[0]

            res = requests.get(output_url)
            if res.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(res.content)
                print(f"[저장완료] {save_path}")
                return f"/static/tongue/{file_name}"
            else:
                print(f"[다운로드 실패] {output_url}, status: {res.status_code}")
                return None
        except Exception as e:
            print(f"영상 생성 실패: {e}")
            return None

    async def _populate_syllable_gpt_tips(self, syllable_chars: Iterable[str]) -> None:
        target_chars = set(syllable_chars)
        if not target_chars:
            return

        # ───────────────────────────────
        # 1) 이미 DB에 있는지 조사 (세션1)
        # ───────────────────────────────
        session = self.db.get_session()
        try:
            existing_rows = session.query(Syllable).filter(Syllable.syllable_char.in_(target_chars)).all()
            existing_map = {row.syllable_char: row for row in existing_rows}
        finally:
            session.close()

        # GPT가 필요한 음절
        need_gpt = [
            ch for ch in target_chars
            if not (row := existing_map.get(ch)) or not row.gpt_tip
        ]
        if not need_gpt:
            return

        # ───────────────────────────────
        # 2) GPT 호출을 동시 실행
        # ───────────────────────────────
        async def fetch_tip(ch: str):
            tip = await self.gpt_service.ask(
                f"너는 어린이 발음 교정 선생님이야."
                f"다음은 한글 음절을 정확하게 발음하는 방법을 설명하는 예시야:"
                f"예시:"
                f"‘학’ 발음을 할 때는 혀끝을 아랫니 뒤에 가볍게 대고, 혀의 뒷부분을 입천장 뒤쪽으로 힘껏 들어올렸다가 ‘탁!’ 하고 터뜨려보세요. 숨을 잠시 막는 느낌이 중요해요."
                f"아래에 주어진 음절에 대해서도 같은 형식과 어조로 짧고 구체적인 발음 팁을 설명해줘."
                f"- 대상 음절: '{ch}'"
                f"※ 형식:"
                f"- '‘{ch}’ 발음을 할 때는 ~' 으로 시작해줘."
                f"- 입 모양, 혀의 위치, 공기의 흐름을 설명해줘."
                f"- 너무 딱딱하지 않고, 친절한 구어체로 말해줘."
                f"- 한 문장으로 요약해줘."
                f"- 표준어를 사용해줘."
                f"- 어린아이에게 설명하듯 쉬운 단어를 사용해줘."
            )
            return ch, tip

        tips = await asyncio.gather(*(fetch_tip(ch) for ch in need_gpt))

        # ───────────────────────────────
        # 3) 한 트랜잭션에 INSERT/UPDATE (세션2)
        # ───────────────────────────────
        session = self.db.get_session()
        try:
            for ch, gpt_tip in tips:
                if not gpt_tip:
                    continue

                # ⚡ 두 번째 세션에서 반드시 직접 select!
                row = session.query(Syllable).filter_by(syllable_char=ch).first()
                if row:
                    row.gpt_tip = gpt_tip  # UPDATE
                else:
                    session.add(
                        Syllable(
                            syllable_char=ch,
                            tongue_url=VISEME_TABLE.get(ch, None),
                            gpt_tip=gpt_tip,
                        )
                    )
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            print(f"[{', '.join(target_chars)}] GPT 팁 저장 오류: {e}")
        finally:
            session.close()

    async def evaluate(self, original_text: str, reference_text: str, audio_path: str) -> dict:
        unique_syllable = extract_unique_syllables(reference_text)
        await self._populate_syllable_gpt_tips(unique_syllable)
        parsed, assessment_result = self.run_azure_evaluation(reference_text, audio_path)
        word_phoneme_scores = self.parse_evaluation_result(parsed)
        feedback = self.map_to_feedback(word_phoneme_scores)
        original_words = original_text.split()
        word_feedbacks = self.transform_pronunciation_data(word_phoneme_scores, original_words)

        return {
            "reference_text": reference_text,
            "accuracy_score": assessment_result.accuracy_score,
            "fluency_score": assessment_result.fluency_score,
            "completeness_score": assessment_result.completeness_score,
            "feedback": feedback,
            "word_feedbacks": word_feedbacks
        }

    def run_azure_evaluation(self, reference_text: str, audio_path: str):
        speech_config = speechsdk.SpeechConfig(
            subscription=self.config.azure_key,
            region=self.config.azure_region
        )
        speech_config.speech_recognition_language = "ko-KR"
        audio_config = speechsdk.AudioConfig(filename=audio_path)

        recognizer = speechsdk.SpeechRecognizer(speech_config, audio_config)

        pronunciation_config = speechsdk.PronunciationAssessmentConfig(
            reference_text=reference_text,
            grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
            granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
            enable_miscue=True
        )
        pronunciation_config.apply_to(recognizer)
        result = recognizer.recognize_once()

        if result.reason == speechsdk.ResultReason.Canceled:
            cancellation = speechsdk.CancellationDetails(result)
            raise Exception(f"Speech canceled: {cancellation.reason}, {cancellation.error_details}")

        parsed = json.loads(result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonResult))
        assessment_result = speechsdk.PronunciationAssessmentResult(result)
        return parsed, assessment_result

    def parse_evaluation_result(self, parsed_json: dict):
        word_scores = []
        try:
            for word in parsed_json["NBest"][0]["Words"]:
                word_text = word.get("Word", "")
                phonemes = word.get("Phonemes", [])
                errtype = word.get("PronunciationAssessment", {}).get("ErrorType", "None")
                scores = [p.get("PronunciationAssessment", {}).get("AccuracyScore") for p in phonemes if
                          p.get("PronunciationAssessment")]
                scores = [s for s in scores if s is not None]
                word_scores.append((word_text, phonemes, scores, errtype))
        except Exception as e:
            print(f"[Parse Error]: {e}")
        return word_scores

    def map_to_feedback(self, word_phoneme_scores: list):
        adjusted_word_phoneme_scores = [
            (word_text, scores_list, errtype_str)
            for word_text, azure_phonemes_list, scores_list, errtype_str in word_phoneme_scores
        ]
        feedback = map_jamos_with_scores(adjusted_word_phoneme_scores)

        for f_word_feedback in feedback:
            scores_for_avg = [s["score"] for s in f_word_feedback["scores"] if "score" in s]
            f_word_feedback["average_score"] = round(sum(scores_for_avg) / len(scores_for_avg),
                                                     2) if scores_for_avg else 0.0

        return feedback

    def save_to_practice_tables(self, user_idx: int, original_text: str, result: dict) -> str:
        session: Session = self.db.get_session()
        try:
            new_session = self.create_practice_session(
                session,
                user_idx=user_idx,
                sentence_text=result["reference_text"],
                accuracy=result["accuracy_score"],
                fluency=result["fluency_score"],
                completeness=result["completeness_score"],
                original_text=original_text
            )

            original_words = original_text.strip().split()
            all_scores = []
            for i, word_info_dict in enumerate(result["feedback"]):
                true_word = original_words[i] if i < len(original_words) else word_info_dict["word"]
                word_idx = self.get_or_create_word_idx(session, true_word)
                practice_word = self.create_practice_word(session, new_session, word_idx, word_info_dict, user_idx)

                jamo_scores_for_db = []

                for jamo_info in word_info_dict["scores"]:
                    if "score" in jamo_info and jamo_info["score"] is not None:
                        jamo_scores_for_db.append({
                            "jamo": jamo_info.get("jamo", ""),
                            "score": jamo_info["score"],
                            "position": jamo_info.get("position", "NONE")
                        })

                self.save_jamo_scores(session, practice_word, jamo_scores_for_db)
                all_scores.extend(jamo_scores_for_db)

            self.update_jamo_statistics(session, user_idx, all_scores)
            session_id = new_session.session_idx
            session.commit()
            return session_id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def create_practice_session(self, db_session, user_idx, sentence_text, accuracy, fluency, completeness,
                                original_text):
        session_obj = PracticeSession(
            session_idx=str(uuid4()),
            user_idx=user_idx,
            sentence_text=sentence_text,
            accuracy_score=accuracy,
            fluency_score=fluency,
            completeness_score=completeness,
            created_at=datetime.datetime.utcnow(),
            original_text=original_text
        )
        db_session.add(session_obj)
        return session_obj

    def get_or_create_word_idx(self, db_session, word_text: str) -> str:
        word = db_session.query(Word).filter_by(text=word_text).first()
        if word:
            return word.word_idx
        pronunciation = KoG2Padvanced(word_text)
        new_word = Word(word_idx=str(uuid4()), text=word_text, pronunciation=pronunciation)
        db_session.add(new_word)
        return new_word.word_idx

    def create_practice_word(self, db_session, session: PracticeSession, word_idx: str, word_info: dict, user_idx=None):
        practice_word = PracticeWord(
            practice_word_idx=str(uuid4()),
            session_idx=session.session_idx,
            word_idx=word_idx,
            spoken_text=word_info["word"],
            average_score=word_info.get("average_score", 0.0),
            error_type=word_info.get("errtype", "None"),
            user_idx=user_idx
        )
        db_session.add(practice_word)
        return practice_word

    def save_jamo_scores(self, db_session: Session, practice_word: PracticeWord, scores: list):
        for jamo_info in scores:
            jamo_position_str = jamo_info.get("position")
            try:
                jamo_position_enum = PracticeWordPosition(jamo_position_str) if jamo_position_str else None
            except ValueError:
                jamo_position_enum = None

            db_session.add(PronunciationScore(
                score_idx=str(uuid4()),
                practice_word_idx=practice_word.practice_word_idx,
                jamo_char=jamo_info["jamo"],
                score=jamo_info["score"],
                jamo_position=jamo_position_enum
            ))

    def update_jamo_statistics(self, db_session, user_idx: int, scores: list):
        from collections import defaultdict

        counter = defaultdict(lambda: {"attempt_count": 0, "total_score": 0.0})
        for s in scores:
            jamo_char = s["jamo"]
            score = s["score"]
            counter[jamo_char]["attempt_count"] += 1
            counter[jamo_char]["total_score"] += score

        existing_stats = {
            stat.jamo_char: stat
            for stat in db_session.query(JamoStatistic).filter(
                JamoStatistic.user_idx == user_idx,
                JamoStatistic.jamo_char.in_(counter.keys())
            ).all()
        }

        for jamo_char, data in counter.items():
            if jamo_char in existing_stats:
                stat = existing_stats[jamo_char]
                stat.attempt_count += data["attempt_count"]
                stat.total_score += data["total_score"]
            else:
                db_session.add(JamoStatistic(
                    user_idx=user_idx,
                    jamo_char=jamo_char,
                    attempt_count=data["attempt_count"],
                    total_score=data["total_score"]
                ))

    def update_user_practice_summary(self, user_idx):
        session: Session = self.db.get_session()
        today = datetime.datetime.utcnow().date()
        start_date = today - datetime.timedelta(days=29)
        yesterday = today - datetime.timedelta(days=1)
        try:
            all_sessions = session.query(PracticeSession).filter(
                PracticeSession.user_idx == user_idx,
                PracticeSession.created_at >= datetime.datetime.combine(start_date, datetime.time.min),
                PracticeSession.created_at <= datetime.datetime.combine(today, datetime.time.max),
            ).all()
            all_scores = [s.accuracy_score for s in all_sessions]
            current_avg = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0

            prev_sessions = session.query(PracticeSession).filter(
                PracticeSession.user_idx == user_idx,
                PracticeSession.created_at >= datetime.datetime.combine(start_date, datetime.time.min),
                PracticeSession.created_at <= datetime.datetime.combine(yesterday, datetime.time.max),
            ).all()
            prev_scores = [s.accuracy_score for s in prev_sessions]
            previous_avg = round(sum(prev_scores) / len(prev_scores), 2) if prev_scores else 0.0

            sessions_by_date = set(s.created_at.date() for s in all_sessions)
            streak = 0
            check_date = today
            while check_date in sessions_by_date:
                streak += 1
                check_date -= datetime.timedelta(days=1)
                if check_date < start_date:
                    break

            total_count = len(all_sessions)

            user = session.query(User).filter(User.user_idx == user_idx).first()
            if user:
                user.practice_streak = streak
                user.total_practice_count = total_count
                user.current_average_accuracy = current_avg
                user.previous_average_accuracy = previous_avg

            session.commit()
        except Exception as e:
            session.rollback()
            raise

    def transform_pronunciation_data(self, raw_data: List, original_words: List) -> List[Dict]:
        session: Session = self.db.get_session()
        result = []

        try:
            for (word, phonemes, scores, error_type), original_word in zip(raw_data, original_words):
                avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
                syllables = []

                for syllable_char in extract_unique_syllables(word):
                    syllable_obj = session.query(Syllable).filter_by(syllable_char=syllable_char).first()
                    syllables.append({
                        "char": syllable_char,
                        "tongue_url": json.loads(
                            syllable_obj.tongue_url) if syllable_obj and syllable_obj.tongue_url else [],
                        "gpt_tip": syllable_obj.gpt_tip if syllable_obj else ""
                    })

                result.append({
                    "word": original_word,
                    "average_score": avg_score,
                    "errtype": error_type,
                    "syllables": syllables,
                    "video_url": None
                })

            return result
        finally:
            session.close()

    def save_practice_filtered(
            self,
            user_idx: int,
            original_text: str,
            result: dict,
            matched_words: set[str],
    ) -> str:
        """
        - `matched_words` 에 들어있는 단어만 PracticeWord/PronunciationScore 로 저장
        """
        session: Session = self.db.get_session()
        try:
            new_session = self.create_practice_session(
                session,
                user_idx=user_idx,
                sentence_text=result["reference_text"],
                accuracy=result["accuracy_score"],
                fluency=result["fluency_score"],
                completeness=result["completeness_score"],
                original_text=original_text,
            )

            # Azure-feedback 은 reference 순서를 그대로 반환
            for fb in result["feedback"]:
                if fb["word"] not in matched_words:
                    continue  # 🔑  필터링 핵심

                word_idx = self.get_or_create_word_idx(session, fb["word"])
                pw = self.create_practice_word(
                    session, new_session, word_idx, fb, user_idx
                )

                jamo_rows = [
                    {
                        "jamo": s["jamo"],
                        "score": s["score"],
                        "position": s.get("position", "NONE"),
                    }
                    for s in fb["scores"]
                    if s.get("score") is not None
                ]
                self.save_jamo_scores(session, pw, jamo_rows)

            session.commit()
            return new_session.session_idx
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # def make_lips_jobs_for_word(word: str) -> list[dict]:
    #     jobs = []
    #     for ch in word:
    #         if re.match(r'^[가-힣]$', ch):
    #             jobs.extend(make_lips_jobs_for_syllable(ch))
    #     return jobs

    def test(self):
        results = extract_lip_movement_sequence("밥을 먹자!")
        all_jobs = []
        for entry in results:
            seq = entry["sequence"]
            all_jobs.extend(make_lips_jobs_from_sequence(seq))

        for job in all_jobs:
            print(job)
