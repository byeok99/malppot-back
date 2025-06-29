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


import json
from typing import List, Any


def extract_word_list(text: str) -> List[str]:
    """GPT 응답 문자열 → 단어 배열(문자열 리스트) 추출."""
    # 1) JSON 파싱
    data: Any = json.loads(text)

    # 2) 📌 케이스 A: 최상위가 배열
    if isinstance(data, list) and all(isinstance(x, str) for x in data):
        return data

    # 3) 📌 케이스 B: 객체 → 값 중 첫 'string 리스트'
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list) and all(isinstance(x, str) for x in value):
                return value

    # 4) 📌 케이스 C: 중첩 구조 (dict → dict → list)
    def dfs(obj):
        if isinstance(obj, list) and all(isinstance(x, str) for x in obj):
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

    # 5) 전부 실패 → 예외
    raise ValueError(f"단어 배열을 찾지 못함: {text[:120]}…")
