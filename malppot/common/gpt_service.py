from openai import OpenAI

from malppot.conf.settings import OpenAIConfig
from malppot.utils.text_utils import extract_word_list


class GPTService:
    def __init__(self, config: OpenAIConfig | dict):
        if isinstance(config, dict):
            self.config = OpenAIConfig(**config)

        self.client = OpenAI(api_key=self.config.api_key)

    async def ask(self, propt: str, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.config.text_model,
            messages=[
                {"role": "system", "content": "너는 친절한 조음 훈련 AI야. 사용자의 발음 교정을 도와줘. 한 문장을 넘기지 말아줘."},
                {'role': 'user', 'content': propt}
            ],
            **kwargs
        )
        return response.choices[0].message.content

    async def ask_recommendation_word(self, jamo: str, num: int, **kwargs) -> list[dict[str, str]]:
        response = self.client.chat.completions.create(
            model=self.config.text_model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "너는 친절한 조음 훈련 AI야. 사용자의 발음 교정을 도와줘."},
                {
                    "role": "user",
                    "content": (
                        f"{jamo} 초성으로 시작하는 표준 한국어 단어 {num}개를 추천해줘.\n"
                        f"규칙:\n"
                        f"1. 모두 {jamo} 초성으로 시작해야 합니다. 유사 초성(예: ㅂ) 단어는 금지입니다.\n"
                        f"2. 두 글자 이상의 단어만 포함하세요 (한 글자 단어 금지).\n"
                        f"3. 각 단어에 대해, 그 단어가 실제로 쓰인 짧은 예문(자연스러운 한국어 문장)도 20글자 이내로 함께 추천해줘.\n"
                        f"4. 반드시 JSON 객체 하나만 반환하세요. 형식: {{'words': [{{'word': '단어1', 'sentence': '예문1'}}, ...] }}\n"
                        f"5. 공식적으로 이용하기 애매한 단어는 제외해주세요.\n"
                        f"6. 포맷을 반드시 지켜야 합니다. 틀리면 오류입니다.\n"
                        f"7. 일상에서 주로 사용하는 단어를 이용해주세요.\n"
                        f"8. 숫자는 포함하지 말아주세요.\n"
                    )
                }
            ],
            **kwargs
        )

        try:
            return extract_word_list(response.choices[0].message.content)
        except ValueError as e:
            raise
