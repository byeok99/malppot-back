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
                mapped_scores.append({"jamo": jamo, "score": 100, "viseme": ""})
                continue

            if score_idx < len(score_list):
                score = score_list[score_idx]
                entry = {"jamo": jamo, "score": score}
                if score <= 70:
                    image = VISEME_TABLE.get(jamo)
                    if image:
                        entry["viseme"] = f"{image}" 
                else:
                    entry["viseme"] = ""
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