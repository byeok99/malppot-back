import re
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

def tag_jamo_roles(hangul: str) -> list[dict]:
    result = []
    for letter in hangul:
        if not re.match(r'^[가-힣]$', letter):
            continue

        chr_code = ord(letter) - GA_CODE
        onset = chr_code // ONSET
        vowel = (chr_code % ONSET) // CODA
        coda = (chr_code % ONSET) % CODA

        result.append({"jamo": ONSET_LIST[onset], "role": "초성"})
        result.append({"jamo": VOWEL_LIST[vowel], "role": "중성"})
        if CODA_LIST[coda]:
            result.append({"jamo": CODA_LIST[coda], "role": "종성"})

    return result

def prepare_interpolation_jobs_from_scores(mapped_data):
    jobs = []

    for word_entry in mapped_data:
        word = word_entry["word"]
        scores = word_entry.get("scores", [])

        if not scores:
            continue

        # 글자 단위로 초중종 분할
        jamo_sets = []
        current_set = []
        for s in scores:
            current_set.append(s)
            if s["role"] == "종성" or len(current_set) == 2:  # 종성이 없을 수도 있음
                jamo_sets.append(current_set)
                current_set = []

        for idx, triplet in enumerate(jamo_sets):
            if len(triplet) < 2:
                continue

            # 자모 경로 준비
            get_path = lambda j: VISEME_TABLE.get(j["jamo"], "")
            onset = next((j for j in triplet if j["role"] == "초성"), None)
            vowel = next((j for j in triplet if j["role"] == "중성"), None)
            coda  = next((j for j in triplet if j["role"] == "종성"), None)

            if onset and vowel:
                onset_path = get_path(onset)
                vowel_path = get_path(vowel)
                if onset_path and vowel_path:
                    jobs.append({
                        "frame1": onset_path,
                        "frame2": vowel_path,
                        "output": f"videos/{word}_{idx}_초성중성.mp4"
                    })

            if vowel and coda:
                vowel_path = get_path(vowel)
                coda_path = get_path(coda)
                if vowel_path and coda_path:
                    jobs.append({
                        "frame1": vowel_path,
                        "frame2": coda_path,
                        "output": f"videos/{word}_{idx}_중성종성.mp4"
                    })

    return jobs

def map_jamos_with_scores(word_score_list: list) -> list:
    result = []
    for word, score_list, errtype in word_score_list:
        jamo_roles = tag_jamo_roles(word)  # [{'jamo': 'ㅇ', 'role': '초성'}, ...]
        mapped_scores = []

        score_idx = 0
        compare_index = 0

        for jr in jamo_roles:
            jamo = jr["jamo"]
            role = jr["role"]

            if role == "초성" and jamo == "ㅇ":
                mapped_scores.append({"jamo": jamo, "role": role, "score": 100})
                continue

            if score_idx < len(score_list):
                score = score_list[score_idx]
                entry = {"jamo": jamo, "role": role, "score": score}
                mapped_scores.append(entry)
                score_idx += 1

            compare_index += 1

        if compare_index != len(score_list):
            print(f"[경고] 자모 수({compare_index})와 점수 수({len(score_list)}) 불일치: '{word}'")
            
            pronspec = "Omission" if compare_index > len(score_list) else "Insertion"
            result.append({
                "word": word,
                "scores": [],
                "errtype": errtype,
                "pronspec": pronspec
            })
            continue

        result.append({
            "word": word,
            "scores": mapped_scores,
            "errtype": errtype,
            "pronspec": ""
        })
    return result