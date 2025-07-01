import os
import re

import pandas as pd

# 한글 분해 상수
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

# CSV에서 viseme 경로를 읽는 함수
KO2PIC_CSV_PATH = 'malppot/domain/speech/feedback/ko2pic.csv'
LIPS_TABLE_CSV_PATH = 'malppot/domain/speech/feedback/lips_table.csv'


def load_viseme_table():
    df = pd.read_csv(KO2PIC_CSV_PATH)
    viseme_dict = dict(zip(df['korean'], df['picture_path_1']))
    return viseme_dict


def load_lips_table():
    df = pd.read_csv(LIPS_TABLE_CSV_PATH)
    lips_dict = dict(zip(df['korean'], df['picture_path_1']))
    return lips_dict


VISEME_TABLE = load_viseme_table()
LIPS_TABLE = load_lips_table()

# 변이음(ㅅ, ㅆ) 구분용
PALATAL_VOWELS = {'ㅣ', 'ㅑ', 'ㅒ', 'ㅕ', 'ㅖ', 'ㅛ', 'ㅠ'}


def get_sibilant_key(onset: str, vowel: str) -> str:
    """
    ㅅ/ㅆ + i계열 모음이면 _palatal, 아니면 _plain
    """
    if onset in {'ㅅ', 'ㅆ'}:
        if vowel in PALATAL_VOWELS:
            return f"변이음{onset}"
        else:
            return f"{onset}"
    return onset


def get_filename_from_url(url: str):
    # URL에서 파일명만 추출 (파라미터 제거)
    return os.path.basename(url).split("?")[0]


def tag_jamo_roles(hangul: str) -> list[dict]:
    """
    한글 음절 → 초/중/종 분해해서 position tagging
    """
    result = []
    for letter in hangul:
        if not re.match(r'^[가-힣]$', letter):
            continue

        chr_code = ord(letter) - GA_CODE
        onset = chr_code // ONSET
        vowel = (chr_code % ONSET) // CODA
        coda = (chr_code % ONSET) % CODA

        result.append({"jamo": ONSET_LIST[onset], "position": "초성"})
        result.append({"jamo": VOWEL_LIST[vowel], "position": "중성"})
        if CODA_LIST[coda]:
            result.append({"jamo": CODA_LIST[coda], "position": "종성"})
    return result


def make_tongue_jobs_for_syllable(ch: str) -> list[dict]:
    """
    초성-중성, 중성-종성의 혀/입모양 frame pair를 만드는 함수.
    변이음(ㅅ/ㅆ), 초성 'ㅎ'의 특수성 반영!
    """
    roles = tag_jamo_roles(ch)
    onset = next((j for j in roles if j["position"] == "초성"), None)
    vowel = next((j for j in roles if j["position"] == "중성"), None)
    coda = next((j for j in roles if j["position"] == "종성"), None)
    jobs = []

    def path(j):
        # 1. ㅅ/ㅆ 변이음 분기
        if j and j["jamo"] in {"ㅅ", "ㅆ"} and j["position"] == "초성":
            v = vowel["jamo"] if vowel else ""
            key = get_sibilant_key(j["jamo"], v)
            return VISEME_TABLE.get(key, "")
        # 2. ㅎ 예외 처리: 초성 'ㅎ' → 모음 frame
        if j and j["jamo"] == "ㅎ" and j["position"] == "초성":
            # return VISEME_TABLE.get(vowel["jamo"], "") if vowel else ""
            return
        # 3. 일반 자모
        return VISEME_TABLE.get(j["jamo"], "") if j else ""

    # [1] 초성→중성 (단, onset이 'ㅎ'이면 frame1도 중성 프레임)
    if onset and vowel and path(onset) and path(vowel):
        frame1 = path(onset)
        frame2 = path(vowel)
        file_name = f"{get_filename_from_url(frame1)}_{get_filename_from_url(frame2)}.mp4"
        jobs.append({
            "letter": ch,
            "frame1": f"https://api.malppot.com/static/images/{frame1}",
            "frame2": f"https://api.malppot.com/static/images/{frame2}",
            "segment": "초성중성",
            "output": file_name
        })

    # [2] 중성→종성 (그대로)
    if vowel and coda and path(vowel) and path(coda):
        frame1 = path(vowel)
        frame2 = path(coda)
        file_name = f"{get_filename_from_url(frame1)}_{get_filename_from_url(frame2)}.mp4"
        jobs.append({
            "letter": ch,
            "frame1": f"https://api.malppot.com/static/images/{frame1}",
            "frame2": f"https://api.malppot.com/static/images/{frame2}",
            "segment": "중성종성",
            "output": file_name
        })

    return jobs


def make_lips_jobs_from_sequence(seq: list) -> list[dict]:
    """
    입모양 sequence(list[str])를 받아
    - 1개: 단독 프레임
    - 2개 이상: 인접 쌍(pair)마다 job
    letter 정보는 포함하지 않음
    """
    jobs = []

    def lips_path(jamo):
        frame = LIPS_TABLE.get(jamo, "")
        return f"https://api.malppot.com/static/images/lips/{frame}" if frame else ""

    # 1개만: 단독 프레임 job
    if len(seq) == 1:
        frame1 = lips_path(seq[0])
        if frame1:
            file_name = f"{get_filename_from_url(frame1)}.png"
            jobs.append({
                "frame1": frame1,
                "frame2": None,
                "segment": "단독",
                "output": file_name
            })
        return jobs

    # 2개 이상: 인접 pair마다 jobs
    for i in range(len(seq) - 1):
        frame1 = lips_path(seq[i])
        frame2 = lips_path(seq[i + 1])
        print(frame1, frame2)
        if frame1 and frame2 and frame1 != frame2:
            file_name = f"{get_filename_from_url(frame1)}_{get_filename_from_url(frame2)}.png"
            jobs.append({
                "frame1": frame1,
                "frame2": frame2,
                "segment": f"{i}to{i + 1}",
                "output": file_name
            })
    return jobs


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


def extract_lip_movement_sequence(hangul: str) -> list:
    """
    한글 단어 입력 시, 각 글자별로 입모양에 영향을 주는 자모만
    초성→중성→종성 순서대로 추출해서 리스트로 반환합니다.
    (단, 초성 ㅎ은 건너뜀, ㅅ/ㅆ은 변이음 구분, lips_table.csv 기준)
    """
    results = []
    for char in hangul:
        if not re.match(r'^[가-힣]$', char):
            continue
        code = ord(char) - GA_CODE
        onset_idx = code // ONSET
        vowel_idx = (code % ONSET) // CODA
        coda_idx = (code % ONSET) % CODA
        onset = ONSET_LIST[onset_idx]
        vowel = VOWEL_LIST[vowel_idx]
        coda = CODA_LIST[coda_idx]
        seq = []

        # 초성
        if onset == 'ㅎ':
            pass
        elif onset in {'ㅅ', 'ㅆ'}:
            sibilant = get_sibilant_key(onset, vowel)
            if sibilant in LIPS_TABLE:
                seq.append(sibilant)
        elif onset in LIPS_TABLE:
            seq.append(onset)
        # 중성
        if vowel in LIPS_TABLE:
            seq.append(vowel)
        # 종성
        if coda and coda != 'ㅎ' and coda in LIPS_TABLE:
            seq.append(coda)
        results.append({"letter": char, "sequence": seq})
    return results
