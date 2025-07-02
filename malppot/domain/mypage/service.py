"""MyPageService – aggregates all My-page statistics for a single user.

Updated 2025‑06‑25:
• 오류 유형 한‑>영 매핑을 확정: Omission→생략, Insertion→첨가, Mispronunciation→왜곡, None→없음
• detailedAnalysis.history 에 과거 점수 추이를 포함 – 동일 단어의 모든 연습 기록을 session.created_at 순서로 수집
"""
from __future__ import annotations

import enum
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, DefaultDict

from sqlalchemy import func

from malppot.common.errors import UserNotFoundException
# --- SQLAlchemy ORM models --------------------------------------------------
from malppot.domain.models import (
    User,
    PracticeSession,
    PracticeWord,
    JamoStatistic,
    PronunciationScore,
)
# --- Pydantic schemas -------------------------------------------------------
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
    PhonemeDetailResponse
)
from malppot.domain.recommendation.service import RecommendationService

# ---------------------------------------------------------------------------
# Helper maps & util functions
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
class MyPageService:
    def __init__(self, db, recommendation_service: RecommendationService):
        self.db_manager = db
        self.recommendation_service = recommendation_service

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

            today = datetime.utcnow().date()
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

                # rec = [
                #     r.text
                #     for r in (
                #         db_session.query(
                #             Word.text, func.avg(PronunciationScore.score).label("avg")
                #         )
                #         .join(PracticeWord, PracticeWord.word_idx == Word.word_idx)
                #         .join(
                #             PronunciationScore,
                #             PronunciationScore.practice_word_idx == PracticeWord.practice_word_idx,
                #         )
                #         .filter(
                #             PracticeWord.user_idx == user_idx,
                #             PronunciationScore.jamo_char == phoneme,
                #         )
                #         .group_by(Word.text)
                #         .order_by(func.avg(PronunciationScore.score))
                #         .limit(4)
                #         .all()
                #     )
                # ]
                rec = self.recommendation_service.get_words(phoneme)

                records = [d for d in detailed if d.phoneme == phoneme]

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
        s = self.db_manager.get_session()  # ─── 상단에 공통 상수 추가 ───────────────────────────────────────────
        CONSONANTS: set[str] = set("ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ")

        try:
            user = s.query(User).filter_by(user_idx=user_idx).first()
            if not user:
                raise UserNotFoundException()

            # ---------- 1) 사용자 기본 정보 ----------------------
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

            # ---------- 2) 7일 그래프 ---------------------------
            today = datetime.utcnow().date()
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

            # ---------- 3) 자음별 평균 점수 ----------------------
            std, tense = "ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎ", "ㄲㄸㅃㅆㅉ"
            normal, strong = {c: 0.0 for c in std}, {c: 0.0 for c in tense}

            for st in (
                    s.query(JamoStatistic)
                            .filter_by(user_idx=user_idx)
                            .all()
            ):
                # ▶︎ 모음 걸러냄
                if not st.attempt_count or st.jamo_char not in CONSONANTS:
                    continue

                acc = round(st.total_score / st.attempt_count, 2)
                if st.jamo_char in normal:
                    normal[st.jamo_char] = acc
                elif st.jamo_char in strong:
                    strong[st.jamo_char] = acc

            # ---------- 4) 종합(에러 분포 etc.) ------------------
            comp = MyPageComprehensiveData(
                errorDistribution=self._error_distribution(s, user_idx),
                soundCategoryAccuracy=_sound_cat_acc({**normal, **strong}),
            )

            return SummaryResponse(
                userData=user_data,
                graphData=graph,
                phonemeAccuracy=normal,
                tenseConsonants=strong,
                comprehensiveData=comp,
            )
        finally:
            s.close()

    async def get_phoneme_detail(self, user_idx: int,
                                 phoneme: str) -> PhonemeDetailResponse:
        s = self.db_manager.get_session()
        try:
            # (1) overall 정확도
            stat: JamoStatistic | None = (
                s.query(JamoStatistic)
                .filter_by(user_idx=user_idx, jamo_char=phoneme)
                .first()
            )
            overall = round((stat.total_score / stat.attempt_count), 2) if stat and stat.attempt_count else 0.0

            # (2) 위치별 분석 + 오류 경향
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
            pos_scores = defaultdict(list)  # {"초성": [score, ...], ...}
            for pos, avg, err, cnt in pos_rows:
                # avg는 error_type별 평균이므로 cnt만큼 점수를 복원
                # 실제로는 (원본 데이터면 score를 바로 모으는게 가장 좋음)
                # 여기선 avg*cnt로 임시 복원 (실제점수 대신)
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

            # (3) AI 추천 단어
            rec = self.recommendation_service.get_words(phoneme)

            # (4) 상세 기록-history
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
        """
        PracticeWord.error_type 비율을 계산해
        MyPageErrorDistribution(pydantic) 객체로 돌려준다.
        """
        rows = (
            s.query(PracticeWord.error_type, func.count())
            .filter(PracticeWord.user_idx == user_idx)
            .group_by(PracticeWord.error_type)
            .all()
        )
        total = sum(c for _e, c in rows) or 1

        # 한글 키 기준 %
        kor_dist = {"생략": 0, "첨가": 0, "왜곡": 0, "없음": 0}
        for err_enum, cnt in rows:
            kor = _err_enum_to_kor(err_enum)
            kor_dist[kor] = round(cnt / total * 100)

        # pydantic 필드 순서는 영어 enum 이름 사용
        return MyPageErrorDistribution(
            Omission=kor_dist["생략"],
            Insertion=kor_dist["첨가"],
            Mispronunciation=kor_dist["왜곡"],
            None_=kor_dist["없음"],
        )

    @staticmethod
    def _get_initial_jamo(syllable: str) -> str:
        """
        한글 완성형 음절을 받아 초성(ㄱ·ㄲ·…·ㅎ)을 반환.
        한글이 아니면 빈 문자열.
        """
        code = ord(syllable)
        if 0xAC00 <= code <= 0xD7A3:
            index = (code - 0xAC00) // 588
            return _INITIALS[index]
        return ""

    def _collect_word_records(
            self, s, user_idx: int, phoneme: str
    ) -> list[MyPageDetailedAnalysisItem]:
        """
        • **첫 글자 초성이 phoneme 인 단어만**
        • **동일 단어는 1개 레코드** ⇒ 최근 연습 기준 accuracy, 나머지는 history
        """
        # 세션 → 날짜 매핑
        session_dates = dict(
            s.query(PracticeSession.session_idx, PracticeSession.created_at)
            .filter(PracticeSession.user_idx == user_idx)
            .all()
        )

        # word_text → (latest_score, error_type, [history_scores])
        acc_map: dict[str, tuple[float, str, list[float]]] = {}

        # phoneme 필터 + 첫글자 초성 필터
        base_q = (
            s.query(PracticeWord, PronunciationScore)
            .join(PronunciationScore,
                  PronunciationScore.practice_word_idx == PracticeWord.practice_word_idx)
            .filter(
                PracticeWord.user_idx == user_idx,
                PronunciationScore.jamo_char == phoneme,
            )
        )

        for pw, ps in base_q.all():
            word_txt = pw.word.text
            if self._get_initial_jamo(word_txt[0]) != phoneme:  # ▶︎ 초성 필터
                continue

            # history 에 넣기 위해 점수 모으기
            created_at = session_dates.get(pw.session_idx)
            if created_at is None:  # 방어
                continue

            latest_score = round(float(ps.score), 2)
            error_type = _err_enum_to_kor(pw.error_type)

            if word_txt not in acc_map:
                acc_map[word_txt] = (latest_score, error_type, [latest_score])
            else:
                # 기록 누적 (정렬은 후에)
                acc_map[word_txt][2].append(latest_score)
                # 더 최근 연습이면 최신-점수/오류 교체
                prev_latest_date = max(session_dates.get(r.session_idx)
                                       for r, _ in base_q
                                       if r.word.text == word_txt)
                if created_at and created_at >= prev_latest_date:
                    acc_map[word_txt] = (latest_score, error_type, acc_map[word_txt][2])

        # 날짜 순으로 history 정렬
        result: list[MyPageDetailedAnalysisItem] = []
        for word, (latest, err, hist) in acc_map.items():
            hist_sorted = sorted(hist)  # 이미 최신이 맨 끝이므로 간단 정렬
            result.append(
                MyPageDetailedAnalysisItem(
                    id=f"{phoneme}-{word}",  # unique id
                    word=word,
                    phoneme=phoneme,
                    accuracy=latest,
                    mainErrorType=err,
                    history=hist_sorted,
                )
            )
        return result


# helpers
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------

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
