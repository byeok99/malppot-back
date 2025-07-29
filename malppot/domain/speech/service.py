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
from malppot.utils.datetime_utils import now_kst, today_kst
from malppot.utils.text_utils import extract_unique_syllables


class SpeechService:
    def __init__(self, config: AzureSpeechConfig, db, gpt_service: GPTService):
        if isinstance(config, dict):
            config = AzureSpeechConfig(**config)
        self.config = config
        self.db = db
        self.gpt_service = gpt_service

    async def convert(self, input_text: str):
        converted_text = KoG2Padvanced(input_text)

        unique_syllable = extract_unique_syllables(converted_text)
        lips_movement = extract_lip_movement_sequence(converted_text)
        input_text = input_text.replace(" ", "")

        asyncio.create_task(self._populate_syllable_tongue_videos(unique_syllable, input_text))
        asyncio.create_task(self._populate_syllable_lips_videos(lips_movement, input_text))

        return {"converted_text": converted_text}

    async def _populate_syllable_tongue_videos(self, syllable_chars: Iterable[str], input_text: str) -> None:
        session: Session = self.db.get_session()
        try:
            syllable_chars = [ori_ch for ori_ch in input_text]
            existing_rows = session.query(Syllable).filter(Syllable.syllable_char.in_(syllable_chars)).all()
            existing_map = {row.syllable_char: row for row in existing_rows}

            for ch, ori_ch in zip(syllable_chars, input_text):
                row = existing_map.get(ori_ch)
                urls = []
                if row and row.tongue_url:
                    try:
                        urls = json.loads(row.tongue_url)
                    except Exception:
                        urls = None
                if urls:
                    continue

                jobs = make_tongue_jobs_for_syllable(ch)
                video_urls = []

                for job in jobs:
                    if job['segment'] == '단독':
                        frame1_path = job['frame']
                        # URL, 경로 뭐든 파일명만 뽑아서 씀
                        filename = os.path.basename(frame1_path)
                        video_url = f"/static/images/{filename}"
                    else:
                        video_url = await self.make_single_video(job, 'tongue')
                    if video_url:
                        video_urls.append(str(video_url))

                if row:
                    row.tongue_url = json.dumps(video_urls, ensure_ascii=False)  # update만!
                else:
                    session.add(
                        Syllable(
                            syllable_char=ori_ch,
                            tongue_url=json.dumps(video_urls, ensure_ascii=False)
                        )
                    )
            session.commit()
        finally:
            session.close()

    async def _populate_syllable_lips_videos(self, lips_movement: Iterable[dict], input_text: str) -> None:
        session: Session = self.db.get_session()
        try:
            syllable_chars = [ori_ch for ori_ch in input_text]
            existing_rows = session.query(Syllable).filter(Syllable.syllable_char.in_(syllable_chars)).all()
            existing_map = {row.syllable_char: row for row in existing_rows}

            for entry, ori_ch in zip(lips_movement, input_text):
                ch = entry["letter"]
                seq = entry["sequence"]
                row = existing_map.get(ori_ch)
                urls = []
                if row and row.lips_url:
                    try:
                        urls = json.loads(row.lips_url)
                    except Exception:
                        urls = None
                if urls:
                    continue

                jobs = make_lips_jobs_from_sequence(seq)

                video_urls = []
                for job in jobs:
                    if job['segment'] == '단독':
                        frame1_path = job['frame1']
                        # URL, 경로 뭐든 파일명만 뽑아서 씀
                        filename = os.path.basename(frame1_path)
                        video_url = f"/static/images/lips/{filename}"
                    else:
                        video_url = await self.make_single_video(job, 'lips')
                    if video_url:
                        video_urls.append(str(video_url))

                if row:
                    row.lips_url = json.dumps(video_urls, ensure_ascii=False)  # update
                else:

                    session.add(Syllable(
                        syllable_char=ori_ch,
                        lips_url=json.dumps(video_urls, ensure_ascii=False)
                    ))
            session.commit()
        finally:
            session.close()

    def get_filename_from_url(url: str):
        return os.path.basename(url).split("?")[0]

    async def make_single_video(self, job, type):
        os.environ["REPLICATE_API_TOKEN"] = self.config.replicate_key
        client = replicate.Client()

        if type == 'tongue':
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
            if type == 'tongue':
                path = f"/static/tongue/{file_name}"
            else:
                path = f"/static/lips/{file_name}"
            return path

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
                if type == 'tongue':
                    path = f"/static/tongue/{file_name}"
                else:
                    path = f"/static/lips/{file_name}"
                return path
            else:
                print(f"[다운로드 실패] {output_url}, status: {res.status_code}")
                return None
        except Exception as e:
            print(f"영상 생성 실패: {e}")
            return None

    async def _populate_syllable_gpt_tips(self, syllable_chars: Iterable[str]) -> None:
        target_chars = set()

        for word in syllable_chars:
            target_chars.update(list(word))

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
                            lips_url=VISEME_TABLE.get(ch, None),
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
        original_words = original_text.split()
        await self._populate_syllable_gpt_tips(original_words)
        parsed, assessment_result = self.run_azure_evaluation(reference_text, audio_path)

        word_phoneme_scores = self.parse_evaluation_result(parsed)
        feedback = self.map_to_feedback(word_phoneme_scores)
        word_feedbacks = self.transform_pronunciation_data(word_phoneme_scores, original_words)

        if word_feedbacks:
            scores = [
                w.get("average_score") if w.get("average_score") is not None else 0.0
                for w in word_feedbacks
            ]
            avg_score = sum(scores) / (len(scores) or 1)
            avg_score = round(avg_score, 2)
        else:
            avg_score = 0.0

        return {
            "reference_text": reference_text,
            "accuracy_score": avg_score,
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
                word_assessment = word.get("PronunciationAssessment", {})
                word_score = word_assessment.get("AccuracyScore")  # ⬅️ 진짜 단어 점수!
                errtype = word_assessment.get("ErrorType", "None")
                phoneme_scores = [
                    p.get("PronunciationAssessment", {}).get("AccuracyScore")
                    for p in phonemes if p.get("PronunciationAssessment")
                ]
                phoneme_scores = [s for s in phoneme_scores if s is not None]
                word_scores.append({
                    "word": word_text,
                    "word_score": word_score,
                    "phonemes": phonemes,
                    "phoneme_scores": phoneme_scores,
                    "errtype": errtype
                })
        except Exception as e:
            print(f"[Parse Error]: {e}")
        return word_scores

    def map_to_feedback(self, word_phoneme_scores: list):
        adjusted_word_phoneme_scores = [
            (entry["word"], entry["phoneme_scores"], entry["errtype"])
            for entry in word_phoneme_scores
        ]
        feedback = map_jamos_with_scores(adjusted_word_phoneme_scores)
        # 각 feedback["average_score"] = entry["word_score"]로 직접 대입
        for entry, fb in zip(word_phoneme_scores, feedback):
            fb["average_score"] = entry["word_score"] if entry.get("word_score") is not None else 0.0
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
            for (i, word_info_dict), word in zip(enumerate(result["feedback"]), original_words):

                true_word = original_words[i] if i < len(original_words) else word_info_dict["word"]
                word_idx = self.get_or_create_word_idx(session, true_word)
                practice_word = self.create_practice_word(session, new_session, word_idx, word_info_dict, word,
                                                          user_idx)

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
            created_at=now_kst(),
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

    def create_practice_word(self, db_session, session: PracticeSession, word_idx: str, word_info: dict, ori_word: str,
                             user_idx=None):
        practice_word = PracticeWord(
            practice_word_idx=str(uuid4()),
            session_idx=session.session_idx,
            word_idx=word_idx,
            spoken_text=ori_word,
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
        today = today_kst()
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
        finally:
            session.close()

    def transform_pronunciation_data(self, raw_data: List[dict], original_words: List[str]) -> List[Dict]:
        session: Session = self.db.get_session()
        result = []
        try:
            for idx, original_word in enumerate(original_words):
                if idx < len(raw_data):
                    entry = raw_data[idx]
                    avg_score = entry.get("word_score", 0.0)
                    errtype = entry.get("errtype", "None")
                else:
                    # 인식결과가 부족하면 0점 처리 (혹은 None)
                    avg_score = 0.0
                    errtype = "None"
                syllables = []
                for syllable_char in extract_unique_syllables(original_word):
                    syllable_obj = session.query(Syllable).filter_by(syllable_char=syllable_char).first()
                    syllables.append({
                        "char": syllable_char,
                        "tongue_url": json.loads(
                            syllable_obj.tongue_url) if syllable_obj and syllable_obj.tongue_url else None,
                        "lips_url": json.loads(
                            syllable_obj.lips_url) if syllable_obj and syllable_obj.lips_url else None,
                        "gpt_tip": syllable_obj.gpt_tip if syllable_obj else ""
                    })
                result.append({
                    "word": original_word,
                    "average_score": avg_score,
                    "errtype": errtype,
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

    def get_syllable_detail(self, char: str) -> dict:
        """
        DB에서 해당 음절의 혀모양, 입모양, gpt_tip을 조회해 dict로 반환
        """
        session: Session = self.db.get_session()
        try:
            row = session.query(Syllable).filter_by(syllable_char=char).first()
            if not row:
                return {
                    "char": char,
                    "tongue_url": [],
                    "lips_url": [],
                    "gpt_tip": ""
                }
            tongue_url = []
            lips_url = []
            if row.tongue_url:
                try:
                    tongue_url = json.loads(row.tongue_url)
                except Exception:
                    tongue_url = []
            if row.lips_url:
                try:
                    lips_url = json.loads(row.lips_url)
                except Exception:
                    lips_url = []
            return {
                "char": char,
                "tongue_url": tongue_url,
                "lips_url": lips_url,
                "gpt_tip": row.gpt_tip or ""
            }
        finally:
            session.close()

    def test(self):
        results = extract_lip_movement_sequence("배")
        all_jobs = []
        for entry in results:
            seq = entry["sequence"]
            all_jobs.extend(make_lips_jobs_from_sequence(seq))

        for job in all_jobs:
            print(job)
