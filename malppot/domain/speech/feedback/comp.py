import re
from collections import defaultdict

import pandas as pd

GA_CODE = 44032
ONSET = 588
CODA = 28

ONSET_LIST = (
    'ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ',
    'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'
)

VOWEL_LIST = (
    'ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ',
    'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ',
    'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ'
)

CODA_LIST = (
    '', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ',
    'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ',
    'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ',
    'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'
)

ALLOWED_JAMOS = set(ONSET_LIST + VOWEL_LIST + CODA_LIST)
KO2PIC_CSV_PATH = 'malppot/domain/speech/feedback/ko2pic.csv'


def load_viseme_table():
    df = pd.read_csv(KO2PIC_CSV_PATH)
    viseme_dict = dict(zip(df['korean'], df['picture_path_1']))
    return viseme_dict


VISEME_TABLE = load_viseme_table()


def _split_triplets(jamo_list: list[dict]) -> list[list[dict]]:
    """
    tag_jamo_roles() 결과(초·중·종 나열) → 글자별 목록으로 묶어 준다.
    (종성이 없는 글자는 2개 길이)
    """
    triplets, buf = [], []
    for j in jamo_list:
        buf.append(j)
        if j["position"] == "종성" or len(buf) == 2:  # 종성 없을 때는 초·중만
            triplets.append(buf)
            buf = []
    if buf:
        triplets.append(buf)
    return triplets


def map_jamos_with_scores(word_score_list: list) -> list:
    result = []
    for word, score_list, errtype in word_score_list:
        jamo_roles = tag_jamo_roles(word)
        mapped_scores = []

        jamo_len = len(jamo_roles)
        score_len = len(score_list)

        for i in range(jamo_len):
            jr = jamo_roles[i]
            jamo = jr["jamo"]
            role = jr["position"]

            if role == "초성" and jamo == "ㅇ":
                mapped_scores.append({
                    "jamo": jamo,
                    "score": 100,
                    "viseme": "",
                    "position": role
                })
                continue

            # 실제 점수가 존재하면 매핑
            if i < score_len:
                score = score_list[i]
                entry = {
                    "jamo": jamo,
                    "score": score,
                    "position": role,
                }
                if score <= 70:
                    image = VISEME_TABLE.get(jamo)
                    entry["viseme"] = image if image else ""
                else:
                    entry["viseme"] = ""
            else:
                # 점수가 없는 경우: Omission 처리
                entry = {
                    "jamo": jamo,
                    "score": 0.0,
                    "viseme": "",
                    "position": role,
                }

            mapped_scores.append(entry)

        pronspec = ""
        if jamo_len != score_len:
            print(f"[경고] 자모 수({jamo_len})와 점수 수({score_len}) 불일치: '{word}'")
            pronspec = "Omission" if jamo_len > score_len else "Insertion"

        result.append({
            "word": word,
            "scores": mapped_scores,
            "errtype": errtype,
            "pronspec": pronspec
        })

    return result


def tag_jamo_roles(hangul: str) -> list[dict]:
    result = []
    for letter in hangul:
        if not re.match(r'^[가-힣]$', letter):
            continue

        chr_code = ord(letter) - GA_CODE
        onset = chr_code // ONSET
        vowel = (chr_code % ONSET) // CODA
        coda = (chr_code % ONSET) % CODA

        result.append({"jamo": ONSET_LIST[onset], "position": "초성"})
        result.append({"jamo": VOWEL_LIST[vowel], "position": "중성"})  # 중성
        if CODA_LIST[coda]:
            result.append({"jamo": CODA_LIST[coda], "position": "종성"})

    return result


def prepare_interpolation_jobs_from_scores(mapped_data: list[dict]) -> list[dict]:
    """
    • `scores` 유무와 관계없이(=Omission이어도) 모든 글자에 대해
      초성→중성, 중성→종성 영상을 만든다.
    • 같은 글자 여러 번 나오면 _1, _2 … 접미사를 붙여 중복 방지.
    """
    jobs: list[dict] = []
    letter_count: defaultdict[str, int] = defaultdict(int)  # 글자별 중복 카운터

    for entry in mapped_data:
        word = entry["word"]
        scores = entry.get("scores", [])

        # 1) 글자 단위 triplet 준비 ------------------------------------------------
        if scores:
            # 이미 position(초성/중성/종성) 정보가 있다
            triplets = _split_triplets(scores)
        else:
            # 점수가 없으면 글자 분해해서 role → position 으로 맞춰 줌
            triplets = _split_triplets(tag_jamo_roles(word))

        # 2) triplet → 영상 job -----------------------------------------------------
        for idx, t in enumerate(triplets):
            if idx >= len(word):  # 방어: 글자수 초과
                continue
            letter = word[idx]

            onset = next((j for j in t if j["position"] == "초성"), None)
            vowel = next((j for j in t if j["position"] == "중성"), None)
            coda = next((j for j in t if j["position"] == "종성"), None)

            def path(j):
                return VISEME_TABLE.get(j["jamo"], "") if j else ""

            def make_name(segment: str) -> str:
                n = letter_count[letter]
                letter_count[letter] += 1
                suffix = "" if n == 0 else f"_{n}"
                return f"videos/{letter}{suffix}_{segment}.mp4"

            # 초성 → 중성
            if onset and vowel and path(onset) and path(vowel):
                jobs.append({
                    "letter": letter,
                    "frame1": path(onset),
                    "frame2": path(vowel),
                    "output": make_name("초성중성"),
                })

            # 중성 → 종성
            if vowel and coda and path(vowel) and path(coda):
                jobs.append({
                    "letter": letter,
                    "frame1": path(vowel),
                    "frame2": path(coda),
                    "output": make_name("중성종성"),
                })

    return jobs


def make_tongue_jobs_for_syllable(ch: str) -> list[dict]:
    roles = tag_jamo_roles(ch)
    onset = next((j for j in roles if j["position"] == "초성"), None)
    vowel = next((j for j in roles if j["position"] == "중성"), None)
    coda = next((j for j in roles if j["position"] == "종성"), None)
    jobs = []

    def path(j):
        return f"https://api.malppot.com/static/images/{VISEME_TABLE.get(j['jamo'], '')}" if j and VISEME_TABLE.get(
            j["jamo"]) else ""

    # 초성→중성
    if onset and vowel and path(onset) and path(vowel):
        jobs.append({
            "letter": ch,
            "frame1": path(onset),
            "frame2": path(vowel),
            "segment": "초성중성",
            "output": f"videos/{ch}_초성중성.mp4"
        })
    # 중성→종성
    if vowel and coda and path(vowel) and path(coda):
        jobs.append({
            "letter": ch,
            "frame1": path(vowel),
            "frame2": path(coda),
            "segment": "중성종성",
            "output": f"videos/{ch}_중성종성.mp4"
        })
    return jobs
