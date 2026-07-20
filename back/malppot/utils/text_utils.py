import re
from typing import List


def extract_unique_syllables(phonetic_string: str) -> List[str]:
    """
    주어진 음성학적 문자열에서 고유한 한글 음절 문자만 추출합니다.
    문자열이 완성형 한글 음절과 공백, 기타 문자로 구성되어 있다고 가정합니다.
    """
    unique_syllables = list()
    korean_syllable_pattern = re.compile(r'[\uAC00-\uD7A3]')

    for char in phonetic_string:
        if korean_syllable_pattern.match(char):
            unique_syllables.append(char)
    return list(unique_syllables)


from typing import Any, List
import json


def extract_word_list(text: str) -> List[Any]:
    """GPT 응답 문자열 → 단어 배열(문자열 리스트 또는 dict 리스트) 추출."""
    # 1) JSON 파싱
    data: Any = json.loads(text)

    # 2) 📌 케이스 A: 최상위가 'string' 배열 (이전 방식 호환)
    if isinstance(data, list) and all(isinstance(x, str) for x in data):
        return data

    # 3) 📌 케이스 B: 최상위가 'dict' 배열 (단어/문장 구조)
    if isinstance(data, list) and all(
            isinstance(x, dict) and "word" in x and "sentence" in x for x in data
    ):
        return data

    # 4) 📌 케이스 C: dict 내부에 'words' key
    if isinstance(data, dict) and "words" in data:
        words = data["words"]
        # string 배열
        if isinstance(words, list) and all(isinstance(x, str) for x in words):
            return words
        # dict 배열 (단어/문장)
        if isinstance(words, list) and all(
                isinstance(x, dict) and "word" in x and "sentence" in x for x in words
        ):
            return words

    # 5) 📌 케이스 D: 중첩 구조 (dfs 탐색)
    def dfs(obj):
        # string 배열
        if isinstance(obj, list) and all(isinstance(x, str) for x in obj):
            return obj
        # dict 배열
        if isinstance(obj, list) and all(
                isinstance(x, dict) and "word" in x and "sentence" in x for x in obj
        ):
            return obj
        if isinstance(obj, dict):
            for v in obj.values():
                found = dfs(v)
                if found:
                    return found
        return None

    maybe = dfs(data)
    if maybe:
        return maybe

    # 6) 실패
    raise ValueError(f"단어 배열(list[str] 또는 list[dict])을 찾지 못함: {text[:120]}…")
