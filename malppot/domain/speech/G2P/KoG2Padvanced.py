# 참고: SpeechFeedback(https://github.com/DevTae/SpeechFeedback) 의 혀, 입 모양 매핑 데이터
# License: Apache License 2.0

__all__ = ["split_syllable_char", "split_syllables",
           "join_jamos", "join_jamos_char",
           "CHAR_INITIALS", "CHAR_MEDIALS", "CHAR_FINALS"]

import itertools
import re

from g2pk import G2p  # g2pk 라이브러리 임포트
from konlpy.tag import Kkma

# g2pk 객체 초기화 (한 번만 수행)
g2p_converter = G2p()
kkma = Kkma()

INITIAL = 0x001
MEDIAL = 0x010
FINAL = 0x100
CHAR_LISTS = {
    INITIAL: list(map(chr, [
        0x3131, 0x3132, 0x3134, 0x3137, 0x3138, 0x3139,
        0x3141, 0x3142, 0x3143, 0x3145, 0x3146, 0x3147,
        0x3148, 0x3149, 0x314a, 0x314b, 0x314c, 0x314d,
        0x314e
    ])),
    MEDIAL: list(map(chr, [
        0x314f, 0x3150, 0x3151, 0x3152, 0x3153, 0x3154,
        0x3155, 0x3156, 0x3157, 0x3158, 0x3159, 0x315a,
        0x315b, 0x315c, 0x315d, 0x315e, 0x315f, 0x3160,
        0x3161, 0x3162, 0x3163
    ])),
    FINAL: list(map(chr, [
        0x3131, 0x3132, 0x3133, 0x3134, 0x3135, 0x3136,
        0x3137, 0x3139, 0x313a, 0x313b, 0x313c, 0x313d,
        0x313e, 0x313f, 0x3140, 0x3141, 0x3142, 0x3144,
        0x3145, 0x3146, 0x3147, 0x3148, 0x314a, 0x314b,
        0x314c, 0x314d, 0x314e
    ]))
}
CHAR_INITIALS = CHAR_LISTS[INITIAL]
CHAR_MEDIALS = CHAR_LISTS[MEDIAL]
CHAR_FINALS = CHAR_LISTS[FINAL]
CHAR_SETS = {k: set(v) for k, v in CHAR_LISTS.items()}
CHARSET = set(itertools.chain(*CHAR_SETS.values()))
CHAR_INDICES = {k: {c: i for i, c in enumerate(v)}
                for k, v in CHAR_LISTS.items()}


def is_hangul_syllable(c):
    return 0xac00 <= ord(c) <= 0xd7a3  # Hangul Syllables


def is_hangul_jamo(c):
    return 0x1100 <= ord(c) <= 0x11ff  # Hangul Jamo


def is_hangul_compat_jamo(c):
    return 0x3130 <= ord(c) <= 0x318f  # Hangul Compatibility Jamo


def is_hangul_jamo_exta(c):
    return 0xa960 <= ord(c) <= 0xa97f  # Hangul Jamo Extended-A


def is_hangul_jamo_extb(c):
    return 0xd7b0 <= ord(c) <= 0xd7ff  # Hangul Jamo Extended-B


def is_hangul(c):
    return (is_hangul_syllable(c) or
            is_hangul_jamo(c) or
            is_hangul_compat_jamo(c) or
            is_hangul_jamo_exta(c) or
            is_hangul_jamo_extb(c))


def is_supported_hangul(c):
    return is_hangul_syllable(c) or is_hangul_compat_jamo(c)


def check_hangul(c, jamo_only=False):
    if not ((jamo_only or is_hangul_compat_jamo(c)) or is_supported_hangul(c)):
        raise ValueError(f"'{c}' is not a supported hangul character. "
                         f"'Hangul Syllables' (0xac00 ~ 0xd7a3) and "
                         f"'Hangul Compatibility Jamos' (0x3130 ~ 0x318f) are "
                         f"supported at the moment.")


def get_jamo_type(c):
    check_hangul(c)
    assert is_hangul_compat_jamo(c), f"not a jamo: {ord(c):x}"
    return sum(t for t, s in CHAR_SETS.items() if c in s)


def split_syllable_char(c):
    check_hangul(c)
    if len(c) != 1:
        raise ValueError("Input string must have exactly one character.")

    init, med, final = None, None, None
    if is_hangul_syllable(c):
        offset = ord(c) - 0xac00
        x = (offset - offset % 28) // 28
        init, med, final = x // 21, x % 21, offset % 28
        if not final:
            final = None
        else:
            final -= 1
    else:
        pos = get_jamo_type(c)
        if pos & INITIAL == INITIAL:
            pos = INITIAL
        elif pos & MEDIAL == MEDIAL:
            pos = MEDIAL
        elif pos & FINAL == FINAL:
            pos = FINAL
        idx = CHAR_INDICES[pos][c]
        if pos == INITIAL:
            init = idx
        elif pos == MEDIAL:
            med = idx
        else:
            final = idx
    return tuple(CHAR_LISTS[pos][idx] if idx is not None else None
                 for pos, idx in
                 zip([INITIAL, MEDIAL, FINAL], [init, med, final]))


def split_syllables(s, ignore_err=True, pad=None):
    # 완성형 음절은 분해하지 않고 그대로 반환하도록 수정
    result = []
    for c in s:
        if is_hangul_syllable(c):
            result.append(c)
        else:
            try:
                result.extend(filter(None, split_syllable_char(c)))
            except Exception:
                if ignore_err:
                    result.append(c)
                else:
                    raise
    return "".join(result)


def join_jamos_char(init, med, final=None):
    chars = (init, med, final)
    for c in filter(None, chars):
        check_hangul(c, jamo_only=True)
    idx = tuple(CHAR_INDICES[pos][c] if c is not None else c
                for pos, c in zip((INITIAL, MEDIAL, FINAL), chars))
    init_idx, med_idx, final_idx = idx
    final_idx = 0 if final_idx is None else final_idx + 1
    return chr(0xac00 + 28 * 21 * init_idx + 28 * med_idx + final_idx)


def join_jamos(s, ignore_err=True):
    # 완성형 음절은 그대로 두고, 자모 3개가 모이면 음절로 조립
    result = []
    buffer = []
    for c in s:
        if c in CHARSET:
            buffer.append(c)
            if len(buffer) == 3:
                try:
                    result.append(join_jamos_char(*buffer))
                except Exception:
                    if ignore_err:
                        result.extend(buffer)
                    else:
                        raise
                buffer = []
        else:
            if buffer:
                result.extend(buffer)
                buffer = []
            result.append(c)
    if buffer:
        # 남은 자모가 2개일 경우 초성+중성만 조합
        if len(buffer) == 2 and all(x in CHARSET for x in buffer):
            try:
                result.append(join_jamos_char(buffer[0], buffer[1]))
            except Exception:
                result.extend(buffer)
        else:
            result.extend(buffer)
    return ''.join(result)


def KoG2Padvanced(Sentence):
    runMorphemeCase = ["의", "히"]

    # Load n-insertion dictionary
    # 실제 파일 경로에 맞춰 수정하거나, 파일이 없을 경우 예외 처리
    nInsertDic = {}
    nInsertList = []
    try:
        nInsertionFile = "malppot/domain/speech/G2P/Dic/nSheetWords.csv"
        with open(nInsertionFile, 'r', encoding='utf-8') as f:
            nInsertionContent = f.readlines()

        for nInsertContent in nInsertionContent:
            nInsertContentList = nInsertContent.split(",")
            if len(nInsertContentList) > 5 and nInsertContentList[1].strip() != "word":
                nInsertDic[nInsertContentList[1].strip()] = nInsertContentList[5].strip()
                nInsertList.append(nInsertContentList[1].strip())
    except FileNotFoundError:
        print("경고: nSheetWords.csv 파일을 찾을 수 없습니다. n-삽입 규칙이 적용되지 않습니다.")
    except Exception as e:
        print(f"경고: nSheetWords.csv 파일 처리 중 오류 발생: {e}. n-삽입 규칙이 적용되지 않습니다.")

    # Main processing
    words = Sentence.split(" ")
    sentence_processed_for_g2p = []  # KoG2P에 전달할 단어 리스트

    for word in words:
        word = word.strip()

        # '의' 발음 규칙 처리 (품사 정보 활용)
        if "의" in word:
            kkma_pos_result = kkma.pos(word)
            word_temp = ""
            for morpheme, pos in kkma_pos_result:
                if morpheme == "의" and pos == "JKG":  # '의'가 조사인 경우
                    word_temp += "에"
                elif morpheme == "의" and pos in ["NNG", "VV", "MAG"]:  # '의'가 명사, 동사, 부사 등인 경우 (예: '의사', '의미하다', '의외로')
                    word_temp += morpheme  # '의'는 그대로 '의' (여기서는 '의' 자체 발음을 유지하도록)
                else:
                    word_temp += morpheme
            word = word_temp

        # '히' 발음 규칙 처리 (기존 로직 유지)
        if "히" in word:
            word_temp = ""
            kkmaDict = dict(kkma.pos(word))
            for key, value in kkmaDict.items():
                jamoInput = split_syllables(key)  # 여기서는 '히' 규칙 적용을 위해 자모 분해
                if "ㅈㅎ" in jamoInput and value == "VV":
                    jamoInput = re.sub("ㅈㅎ", "ㅊ", jamoInput)
                refinedJamo = join_jamos(jamoInput)  # 다시 완성형으로 조립
                word_temp += refinedJamo
            word = word_temp

        # n-insertion
        for nInsertEach in nInsertList:
            if nInsertEach in word:
                word = word.replace(nInsertEach, nInsertDic[nInsertEach])

        sentence_processed_for_g2p.append(word)

    # G2P dictionary (KoG2PDic.txt는 g2pk 사용 시 불필요하므로 이 부분은 삭제하거나 주석 처리)
    # 하지만 원본 코드의 흐름을 유지하기 위해 예외 처리만 남겨둡니다.
    # g2pk는 내부적으로 표준 발음 규칙과 사전을 가지고 있습니다.
    fileDir = "malppot/domain/speech/G2P/Dic/KoG2PDic.txt"  # 이 파일은 g2pk 사용 시 직접적으로 사용되지 않습니다.
    KoG2PDic = {}  # 빈 딕셔너리로 초기화
    try:
        with open(fileDir, 'r', encoding='utf-8') as fr:
            contents = fr.readlines()
        for content in contents:
            KorSim, EngSim = content.replace("\n", "").strip().split("\t")
            KoG2PDic[EngSim] = KorSim
    except FileNotFoundError:
        print("경고: KoG2PDic.txt 파일을 찾을 수 없습니다. (g2pk 사용 시 이 파일은 필수가 아닙니다.)")
    except Exception as e:
        print(f"경고: KoG2PDic.txt 파일 처리 중 오류 발생: {e}. (g2pk 사용 시 이 파일은 필수가 아닙니다.)")

    hangulMo = ["ㅏ", "ㅑ", "ㅓ", "ㅕ", "ㅗ", "ㅛ", "ㅜ", "ㅠ", "ㅡ", "ㅣ", "ㅐ", "ㅘ", "ㅔ", "ㅙ", "ㅚ", "ㅝ", "ㅟ", "ㅞ", "ㅜ", "ㅢ",
                "ㅒ", "ㅖ"]

    totalSentence = []
    # 각 단어에 대해 g2pk를 사용하여 G2P 변환을 수행합니다.
    # g2pk는 단어 단위로 발음 변환을 해주며, 연음, 경음화 등 복잡한 규칙을 자동으로 처리합니다.
    for eachWord in sentence_processed_for_g2p:
        # g2pk.G2p() 인스턴스를 사용하여 단어를 발음 기호로 변환합니다.
        # 이 한 줄이 기존 KoG2P 클래스와 그 아래의 복잡한 자모 조립/규칙 부분을 대체합니다.
        phonetic_word = g2p_converter(eachWord)  # g2pk는 완성된 발음 문자열을 반환합니다.

        # g2pk는 대부분의 음운 변동을 처리해주므로,
        # 기존 코드의 자모 조립, 'ㅇ' 추가, ㅎ 탈락, 위치 동화 등의 로직은
        # g2pk의 결과에 대해 다시 적용할 필요가 없습니다.
        # 만약 g2pk로도 처리되지 않는 아주 예외적인 규칙이 있다면 여기에 추가할 수 있습니다.

        # '예' -> '에' 중화는 g2pk가 처리하지 않을 수 있으므로 명시적으로 적용.
        # g2pk는 발음 기반이므로, '예'를 '에'로 발음하는 것은 일반적으로 처리됩니다.
        # 하지만 만약의 경우를 대비하여 중화 규칙을 다시 확인하는 것이 좋습니다.
        # 여기서는 g2pk의 결과가 완성형 음절이므로, 자모 분리 후 적용하고 다시 합쳐야 합니다.

        # '예' -> '에' 중화는 사실 g2pk가 대부분 처리합니다.
        # 원본 코드의 'KoG2P'가 어떤 기능을 했는지에 따라 이 부분이 필요 없을 수도 있습니다.
        # 예: '계산' -> '게산', '시계' -> '시계' (g2pk는 '시게'로 발음)

        # 만약 '예' -> '에' 규칙을 g2pk 결과에 추가로 적용하고 싶다면:
        # temp_jamo = split_syllables(phonetic_word)
        # temp_jamo = re.sub('(?<=[ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ])ㅖ', 'ㅔ', temp_jamo)
        # phonetic_word = join_jamos(temp_jamo)

        totalSentence.append(phonetic_word)

    # 마지막: 문장 전체를 공백으로 연결하여 최종 결과 반환
    result = ' '.join(totalSentence)
    return result
