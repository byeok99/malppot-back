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

    async def ask_recommendation_word(self, jamo: str, num: int, **kwargs) -> list[str]:
        response = self.client.chat.completions.create(
            model=self.config.text_model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "너는 친절한 조음 훈련 AI야. 사용자의 발음 교정을 도와줘."},
                {'role': 'user', 'content': f"{jamo} 초성으로 시작하는 표준 한국어 단어 {num}개를 추천해줘."
                                            f"규칙"
                                            f"1. 모두 {jamo} 초성으로 시작해야 합니다. 유사 초성(예: ㅂ) 단어는 금지입니다."
                                            f"2. 두 글자 이상의 단어만 포함하세요 (한 글자 단어 금지)."
                                            f"3. 반드시 JSON 객체 하나만 반환하세요. ['words': ['단어1', '단어2', ...] "
                                            f"4. 공식적으로 이용하기 애매한 단어는 제외해주세요."
                                            f"포맷을 지키지 않으면 오류입니다."
                 }
            ],
            **kwargs
        )

        try:
            return extract_word_list(response.choices[0].message.content)
        except ValueError as e:
            raise
