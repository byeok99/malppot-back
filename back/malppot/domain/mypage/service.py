from __future__ import annotations

import enum
from collections import defaultdict
from datetime import timedelta
from typing import Dict, List, Optional, DefaultDict

from sqlalchemy import func

from malppot.common.errors import UserNotFoundException
from malppot.domain.models import (
    User,
    PracticeSession,
    PracticeWord,
    JamoStatistic,
    PronunciationScore,
)
from malppot.domain.mypage.schema import (
    MyPageResponse,
    MyPageUserData,
    Accuracy,
    MyPageGraphDataPoint,
    MyPageDetailedAnalysisItem,
    MyPageComprehensiveData,
    MyPageErrorDistribution,
    PhonemeAnalysis,
    PhonemePositionAnalysis,
    ErrorTendency,
    SummaryResponse,
    PhonemeDetailResponse,
    PatientReport
)
from malppot.domain.recommendation.service import RecommendationService
from malppot.utils.datetime_utils import today_kst

_ERR_ENG2KOR = {
    "Omission": "생략",
    "Insertion": "첨가",
    "Mispronunciation": "왜곡",
    "None": "없음",
}

_KOR2FIELD = {
    "생략": "omission",
    "첨가": "insertion",
    "왜곡": "distortion",
    "없음": "none",  # not displayed in ErrorTendency but 유지
}

_INITIALS = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"


def _err_enum_to_kor(err: Optional[enum.Enum | str]) -> str:
    if isinstance(err, enum.Enum):
        err = err.value
    return _ERR_ENG2KOR.get(err, str(err))


def _kor_to_field(kor: str) -> str:
    return _KOR2FIELD[kor]


class MyPageService:
    def __init__(self, db, recommendation_service: RecommendationService):
        self.db_manager = db
        self.recommendation_service = recommendation_service
        self.CONSONANTS: set[str] = set("ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ")

    async def get_mypage_data(self, user_idx: int) -> MyPageResponse:
        db_session = self.db_manager.get_session()
        try:
            user = db_session.query(User).filter(User.user_idx == user_idx).first()
            if not user:
                raise UserNotFoundException()

            user_data = MyPageUserData(
                userName=user.name if user.name else user.email,
                profileImageUrl=user.profile_image_url,
                practiceStreak=user.practice_streak,
                totalPracticeCount=user.total_practice_count,
                accuracy=Accuracy(
                    previous=user.previous_average_accuracy,
                    current=user.current_average_accuracy,
                ),
            )

            today = today_kst()
            start = today - timedelta(days=6)
            rows = (
                db_session.query(
                    func.date(PracticeSession.created_at),
                    func.avg(PracticeSession.accuracy_score),
                )
                .filter(
                    PracticeSession.user_idx == user_idx,
                    func.date(PracticeSession.created_at) >= start,
                )
                .group_by(func.date(PracticeSession.created_at))
                .all()
            )
            date_map = {
                r[0]: round(float(r[1]), 2) if r[1] is not None else 0.0 for r in rows
            }
            graph = [
                MyPageGraphDataPoint(record_date=start + timedelta(i), score=date_map.get(start + timedelta(i), 0.0))
                for i in range(7)
            ]

            std = "ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎ"
            tense = "ㄲㄸㅃㅆㅉ"
            normal_acc = {c: 0.0 for c in std}
            tense_acc = {c: 0.0 for c in tense}
            for st in db_session.query(JamoStatistic).filter(JamoStatistic.user_idx == user_idx).all():
                if st.attempt_count:
                    score = round(st.total_score / st.attempt_count, 2)
                    if st.jamo_char in normal_acc:
                        normal_acc[st.jamo_char] = score
                    elif st.jamo_char in tense_acc:
                        tense_acc[st.jamo_char] = score
            all_acc: Dict[str, float] = {**normal_acc, **tense_acc}

            detailed: List[MyPageDetailedAnalysisItem] = []
            pw_list: List[PracticeWord] = (
                db_session.query(PracticeWord).filter(PracticeWord.user_idx == user_idx).all()
            )
            session_dates = {
                s.session_idx: s.created_at
                for s in db_session.query(PracticeSession.session_idx, PracticeSession.created_at)
                .filter(PracticeSession.user_idx == user_idx)
                .all()
            }
            for pw in pw_list:
                hist_rows = (
                    db_session.query(PracticeWord)
                    .filter(
                        PracticeWord.user_idx == user_idx,
                        PracticeWord.word_idx == pw.word_idx,
                    )
                    .all()
                )
                hist_sorted = sorted(
                    [
                        (session_dates.get(r.session_idx), r.average_score)
                        for r in hist_rows
                        if r.average_score is not None
                    ],
                    key=lambda t: t[0],
                )
                history_scores = [round(float(s), 2) for _, s in hist_sorted]

                pscore = (
                    db_session.query(PronunciationScore)
                    .filter(PronunciationScore.practice_word_idx == str(pw.practice_word_idx))
                    .first()
                )
                if not pscore or not pscore.jamo_char:
                    continue
                detailed.append(
                    MyPageDetailedAnalysisItem(
                        id=str(pscore.score_idx),
                        word=pw.word.text,
                        phoneme=pscore.jamo_char,
                        accuracy=round(pscore.score, 2),
                        mainErrorType=_err_enum_to_kor(pw.error_type),
                        history=history_scores,
                    )
                )

            err_rows = (
                db_session.query(PracticeWord.error_type, func.count())
                .filter(PracticeWord.user_idx == user_idx)
                .group_by(PracticeWord.error_type)
                .all()
            )
            total = sum(c for _e, c in err_rows) or 1
            dist_kor = {"생략": 0, "첨가": 0, "왜곡": 0, "없음": 0}
            for e, c in err_rows:
                dist_kor[_err_enum_to_kor(e)] = round(c / total * 100)
            dist_eng = {
                "Omission": dist_kor["생략"],
                "Insertion": dist_kor["첨가"],
                "Mispronunciation": dist_kor["왜곡"],
                "None_": dist_kor["없음"],
            }
            comp = MyPageComprehensiveData(
                errorDistribution=MyPageErrorDistribution(**dist_eng),
                soundCategoryAccuracy=_sound_cat_acc(all_acc),
            )

            phoneme_detail: Dict[str, PhonemeAnalysis] = {}
            for phoneme, overall in all_acc.items():
                pos_rows = (
                    db_session.query(
                        PronunciationScore.jamo_position,
                        func.avg(PronunciationScore.score),
                        PracticeWord.error_type,
                        func.count(),
                    )
                    .join(
                        PracticeWord,
                        PracticeWord.practice_word_idx == PronunciationScore.practice_word_idx,
                    )
                    .filter(
                        PracticeWord.user_idx == user_idx,
                        PronunciationScore.jamo_char == phoneme,
                    )
                    .group_by(
                        PronunciationScore.jamo_position, PracticeWord.error_type
                    )
                    .all()
                )
                pos_avg: Dict[str, float] = defaultdict(float)
                pos_err: Dict[str, DefaultDict[str, int]] = defaultdict(lambda: defaultdict(int))
                for pos, avg, err, cnt in pos_rows:
                    pos_avg[pos] = avg
                    pos_err[pos][_err_enum_to_kor(err)] += cnt

                pos_analysis: Dict[str, PhonemePositionAnalysis] = {}
                for p, acc in pos_avg.items():
                    et = ErrorTendency()
                    tot = sum(pos_err[p].values()) or 1
                    for k, c in pos_err[p].items():
                        setattr(et, _kor_to_field(k), round(c / tot * 100))
                    pos_analysis[p] = PhonemePositionAnalysis(
                        averageAccuracy=round(acc, 2),
                        errorTendency=et,
                    )

                rec = self.recommendation_service.get_words(phoneme)
                records = self._collect_word_records(db_session, user_idx, phoneme)
                phoneme_detail[phoneme] = PhonemeAnalysis(
                    overallAccuracy=overall,
                    positionalAnalysis=pos_analysis,
                    recommendedWords=rec,
                    allRecords=records,
                )

            return MyPageResponse(
                userData=user_data,
                graphData=graph,
                phonemeAccuracy=normal_acc,
                tenseConsonants=tense_acc,
                detailedAnalysis=detailed,
                comprehensiveData=comp,
                phonemeDetailedAnalysis=phoneme_detail,
            )
        finally:
            db_session.close()

    async def get_summary(self, user_idx: int) -> SummaryResponse:
        s = self.db_manager.get_session()
        try:
            user = s.query(User).filter_by(user_idx=user_idx).first()
            if not user:
                raise UserNotFoundException()

            user_data = MyPageUserData(
                userName=user.name or user.email,
                profileImageUrl=user.profile_image_url,
                practiceStreak=user.practice_streak,
                totalPracticeCount=user.total_practice_count,
                accuracy=Accuracy(
                    previous=user.previous_average_accuracy,
                    current=user.current_average_accuracy,
                ),
            )

            today = today_kst()
            start = today - timedelta(days=6)
            rows = (
                s.query(func.date(PracticeSession.created_at),
                        func.avg(PracticeSession.accuracy_score))
                .filter(PracticeSession.user_idx == user_idx,
                        func.date(PracticeSession.created_at) >= start)
                .group_by(func.date(PracticeSession.created_at))
                .all()
            )
            m = {d: (float(a) if a else 0.0) for d, a in rows}
            graph = [
                MyPageGraphDataPoint(record_date=start + timedelta(i),
                                     score=round(m.get(start + timedelta(i), 0.0), 2))
                for i in range(7)
            ]

            std, tense = "ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎ", "ㄲㄸㅃㅆㅉ"
            normal, strong = {c: 0.0 for c in std}, {c: 0.0 for c in tense}

            for st in (
                    s.query(JamoStatistic)
                            .filter_by(user_idx=user_idx)
                            .all()
            ):
                if not st.attempt_count or st.jamo_char not in self.CONSONANTS:
                    continue

                acc = round(st.total_score / st.attempt_count, 2)
                if st.jamo_char in normal:
                    normal[st.jamo_char] = acc
                elif st.jamo_char in strong:
                    strong[st.jamo_char] = acc

            return SummaryResponse(
                userData=user_data,
                graphData=graph,
                phonemeAccuracy=normal,
                tenseConsonants=strong
            )
        finally:
            s.close()

    async def get_phoneme_detail(self, user_idx: int, phoneme: str) -> PhonemeDetailResponse:
        s = self.db_manager.get_session()
        try:
            stat: JamoStatistic | None = (
                s.query(JamoStatistic)
                .filter_by(user_idx=user_idx, jamo_char=phoneme)
                .first()
            )
            overall = round((stat.total_score / stat.attempt_count), 2) if stat and stat.attempt_count else 0.0

            pos_rows = (
                s.query(PronunciationScore.jamo_position,
                        func.avg(PronunciationScore.score),
                        PracticeWord.error_type,
                        func.count())
                .join(PracticeWord,
                      PracticeWord.practice_word_idx == PronunciationScore.practice_word_idx)
                .filter(PracticeWord.user_idx == user_idx,
                        PronunciationScore.jamo_char == phoneme)
                .group_by(PronunciationScore.jamo_position,
                          PracticeWord.error_type)
                .all()
            )
            pos_scores = defaultdict(list)
            for pos, avg, err, cnt in pos_rows:
                if avg is not None:
                    pos_scores[pos].extend([avg] * cnt)
            pos_avg = {}
            for pos, scores in pos_scores.items():
                if scores:
                    pos_avg[pos] = sum(scores) / len(scores)
                else:
                    pos_avg[pos] = 0.0

            pos_err: dict[str, DefaultDict[str, int]] = defaultdict(lambda: defaultdict(int))
            for pos, avg, err, cnt in pos_rows:
                pos_err[pos][_err_enum_to_kor(err)] += cnt

            pos_analysis: dict[str, PhonemePositionAnalysis] = {}
            for p, acc in pos_avg.items():
                et = ErrorTendency()
                tot = sum(pos_err[p].values()) or 1
                for k, c in pos_err[p].items():
                    setattr(et, _kor_to_field(k), round(c / tot * 100))
                pos_analysis[p] = PhonemePositionAnalysis(
                    averageAccuracy=round(acc, 2),
                    errorTendency=et,
                )

            rec = self.recommendation_service.get_words(phoneme)
            records = self._collect_word_records(s, user_idx, phoneme)

            return PhonemeDetailResponse(
                phoneme=phoneme,
                detail=PhonemeAnalysis(
                    overallAccuracy=overall,
                    positionalAnalysis=pos_analysis,
                    recommendedWords=rec,
                    allRecords=records,
                ),
            )
        finally:
            s.close()

    def _error_distribution(self, s, user_idx: int) -> MyPageErrorDistribution:
        rows = (
            s.query(PracticeWord.error_type, func.count())
            .filter(PracticeWord.user_idx == user_idx)
            .group_by(PracticeWord.error_type)
            .all()
        )
        total = sum(c for _e, c in rows) or 1

        kor_dist = {"생략": 0, "첨가": 0, "왜곡": 0, "없음": 0}
        for err_enum, cnt in rows:
            kor = _err_enum_to_kor(err_enum)
            kor_dist[kor] = round(cnt / total * 100)

        return MyPageErrorDistribution(
            Omission=kor_dist["생략"],
            Insertion=kor_dist["첨가"],
            Mispronunciation=kor_dist["왜곡"],
            None_=kor_dist["없음"],
        )

    @staticmethod
    def _get_initial_jamo(syllable: str) -> str:
        code = ord(syllable)
        if 0xAC00 <= code <= 0xD7A3:
            index = (code - 0xAC00) // 588
            return _INITIALS[index]
        return ""

    def _collect_word_records(
            self, s, user_idx: int, phoneme: str
    ) -> list[MyPageDetailedAnalysisItem]:
        from malppot.domain.models import Word  # 반드시 import
        session_dates = dict(
            s.query(PracticeSession.session_idx, PracticeSession.created_at)
            .filter(PracticeSession.user_idx == user_idx)
            .all()
        )
        pw_rows = (
            s.query(
                PracticeWord.word_idx,
                Word.text,
                PracticeWord.average_score,
                PracticeWord.error_type,
                PracticeWord.session_idx,
                PracticeSession.created_at
            )
            .join(PracticeSession, PracticeWord.session_idx == PracticeSession.session_idx)
            .join(Word, PracticeWord.word_idx == Word.word_idx)
            .filter(
                PracticeWord.user_idx == user_idx,
                PracticeWord.average_score.isnot(None),
            )
            .order_by(Word.text, PracticeSession.created_at)
            .all()
        )
        from collections import defaultdict
        word_map = defaultdict(list)
        for word_idx, word_txt, avg_score, error_type, session_idx, created_at in pw_rows:
            if self._get_initial_jamo(word_txt[0]) == phoneme:
                word_map[word_txt].append((created_at, avg_score, error_type))
        result: list[MyPageDetailedAnalysisItem] = []
        for word_txt, items in word_map.items():
            items = [x for x in items if x[0] is not None]
            items_sorted = sorted(items, key=lambda x: x[0])
            history_scores = [round(float(avg), 2) for _, avg, _ in items_sorted][-7:]
            _, latest_score, latest_error = items_sorted[-1]
            result.append(
                MyPageDetailedAnalysisItem(
                    id=f"{phoneme}-{word_txt}",
                    word=word_txt,
                    phoneme=phoneme,
                    accuracy=round(float(latest_score), 2),
                    mainErrorType=_err_enum_to_kor(latest_error),
                    history=history_scores
                )
            )
        return result

    def get_report(self, user_idx: int) -> PatientReport:
        s = self.db_manager.get_session()
        try:
            # --- 1. 기본 유저/진단 정보 ---
            user = s.query(User).filter_by(user_idx=user_idx).first()
            if not user:
                raise ValueError("존재하지 않는 유저입니다.")
            name = user.name
            total_count = user.total_practice_count
            streak = user.practice_streak

            # --- 3. 전체 평균 정확도 ---
            overall_acc = round(user.current_average_accuracy or 0.0, 2)

            # --- 4. 자음별 정확도 ---
            stats = (
                s.query(JamoStatistic)
                .filter(JamoStatistic.user_idx == user_idx)
                .all()
            )
            consonant_acc = {
                stat.jamo_char: round(stat.total_score / stat.attempt_count, 2)
                for stat in stats
                if stat.attempt_count > 0 and stat.jamo_char in self.CONSONANTS
            }

            # --- 5. 최근 7일 정확도 변화 ---
            today = today_kst()
            start = today - timedelta(days=6)
            rows = (
                s.query(
                    func.date(PracticeSession.created_at),
                    func.avg(PracticeSession.accuracy_score)
                )
                .filter(
                    PracticeSession.user_idx == user_idx,
                    func.date(PracticeSession.created_at) >= start
                )
                .group_by(func.date(PracticeSession.created_at))
                .all()
            )
            date_map = {d: round(float(a), 2) for d, a in rows}
            accuracy_trend = [
                date_map.get(start + timedelta(i), 0.0)
                for i in range(7)
            ]

            # --- 6. 주의해야할 음소(최저 정확도+위치) ---
            attention_phonemes = self.get_attention_jamo(
                user_idx=user_idx,
                jamo_num=2
            )

            # --- 7. jamo_detail 유형별 통계 ---
            score_rows = (
                s.query(
                    PronunciationScore.jamo_char,
                    PronunciationScore.jamo_position,
                    func.avg(PronunciationScore.score)
                )
                .join(PracticeWord, PracticeWord.practice_word_idx == PronunciationScore.practice_word_idx)
                .filter(
                    PracticeWord.user_idx == user_idx,
                    PronunciationScore.jamo_char.in_(self.CONSONANTS)  # 자음만!
                )
                .group_by(PronunciationScore.jamo_char, PronunciationScore.jamo_position)
                .all()
            )

            error_type_rows = (
                s.query(
                    PronunciationScore.jamo_char,
                    PronunciationScore.jamo_position,
                    PracticeWord.error_type,
                    func.count()
                )
                .join(PracticeWord, PracticeWord.practice_word_idx == PronunciationScore.practice_word_idx)
                .filter(
                    PracticeWord.user_idx == user_idx,
                    PronunciationScore.jamo_char.in_(self.CONSONANTS)  # 자음만!
                )
                .group_by(PronunciationScore.jamo_char, PronunciationScore.jamo_position, PracticeWord.error_type)
                .all()
            )

            attempt_rows = (
                s.query(
                    PronunciationScore.jamo_char,
                    PronunciationScore.jamo_position,
                    func.count()
                )
                .join(PracticeWord, PracticeWord.practice_word_idx == PronunciationScore.practice_word_idx)
                .filter(
                    PracticeWord.user_idx == user_idx,
                    PronunciationScore.jamo_char.in_(self.CONSONANTS)  # 자음만!
                )
                .group_by(PronunciationScore.jamo_char, PronunciationScore.jamo_position)
                .all()
            )
            score_by_jamo_pos = {
                (j, p): round(a, 2) if a is not None else None
                for j, p, a in score_rows or []
            }

            attempt_dict = {(j, p): total for j, p, total in attempt_rows}
            error_by_jamo_pos = defaultdict(list)
            for row in (error_type_rows or []):
                j, p, e, c = row
                total = attempt_dict.get((j, p), 0)
                percent = round((c / total * 100), 1) if total > 0 else 0
                error_by_jamo_pos[(j, p)].append({
                    "error_type": e,
                    "count": c,
                    "percent": percent
                })
            jamo_detail = []
            for (j, p), avg_score in score_by_jamo_pos.items():
                jamo_detail.append({
                    "phoneme": j,
                    "position": p,
                    "average_score": avg_score,
                    "total_attempts": attempt_dict.get((j, p), 0),
                    "error_types": error_by_jamo_pos.get((j, p), [])
                })

            return PatientReport(
                name=name,
                total_practice_count=total_count,
                practice_streak=streak,
                overall_accuracy=overall_acc,
                consonant_scores=consonant_acc,
                seven_day_accuracy_trend=accuracy_trend,
                attention_phonemes=attention_phonemes,
                jamo_detail=jamo_detail,
            )
        finally:
            s.close()

    def get_attention_jamo(self, user_idx: int, jamo_num: int):
        session = self.db_manager.get_session()

        try:
            # 1. 사용자가 연습한 자모 추출
            tried_jamo_set = {
                row[0]
                for row in (
                    session.query(PronunciationScore.jamo_char)
                    .join(PracticeWord, PracticeWord.practice_word_idx == PronunciationScore.practice_word_idx)
                    .filter(
                        PracticeWord.user_idx == user_idx,
                        PronunciationScore.jamo_char.in_(self.CONSONANTS),
                        PronunciationScore.score.isnot(None)
                    )
                    .group_by(PronunciationScore.jamo_char)
                    .all()
                )
            }

            # 2. 자모 + 위치 별 평균 정확도 및 시도 수
            pos_rows = (
                session.query(
                    PronunciationScore.jamo_char,
                    PronunciationScore.jamo_position,
                    func.avg(PronunciationScore.score),
                    func.count(PronunciationScore.score)
                )
                .join(PracticeWord, PracticeWord.practice_word_idx == PronunciationScore.practice_word_idx)
                .filter(
                    PracticeWord.user_idx == user_idx,
                    PronunciationScore.jamo_char.in_(tried_jamo_set)
                )
                .group_by(PronunciationScore.jamo_char, PronunciationScore.jamo_position)
                .all()
            )

            # 3. 정확도 정렬 후 jamo_num개 추출
            filtered_rows = [
                (j, p, a) for j, p, a, cnt in pos_rows if cnt > 0 and a is not None
            ]
            sorted_phonemes = sorted(filtered_rows, key=lambda x: x[2])  # 정확도 오름차순

            return [
                {"phoneme": j, "position": p, "accuracy": round(a, 2)}
                for j, p, a in sorted_phonemes[:jamo_num]
            ]

        except Exception as e:
            print(f"[ERROR] Failed to fetch attention jamo for user {user_idx}: {e}")
            return []

        finally:
            session.close()


def _sound_cat_acc(all_acc: Dict[str, float]) -> Dict[str, float]:
    cat = {
        "예사소리": ["ㄱ", "ㄷ", "ㅂ", "ㅅ", "ㅈ"],
        "된소리": ["ㄲ", "ㄸ", "ㅃ", "ㅆ", "ㅉ"],
        "거센소리": ["ㅋ", "ㅌ", "ㅍ", "ㅊ"],
        "울림소리": ["ㄴ", "ㅁ", "ㅇ", "ㄹ"],
    }
    return {
        k: round(sum(all_acc[p] for p in v) / len(v), 2) for k, v in cat.items()
    }
