# malppot-back

조음 훈련 서비스 [말:뻗] 백엔드

## 개발환경 설정하기

### 파이썬 버전 확인하기

파이썬 버전: 3.11.4 이상이어야 합니다.

```bash
$ python3 --version
Python 3.11.4
```

### 프로젝트 가져오기

```bash
git clone https://github.com/byeok99/malppot-back.git
```

또는 zip파일로 다운받아서 압축을 풀어도 됩니다.

### 패키지 설치하기

```bash
pip install -r requirements.txt
```

## git

> [!IMPORTANT]
> 아래 내용 꼭 읽어보세요!

[Git/Github 사용하기](docs/git.md)

## Reference

- [SpeechFeedback](https://github.com/DevTae/SpeechFeedback)
    - License: Apache License 2.0
    - 사용 목적: 혀, 입 모양 매핑 데이터 활용

## Third-Party APIs & Services

- **Azure Speech Punctuation API**
    - 유형: 유료 API (Microsoft Azure)
    - 사용 목적: 사용자의 발음 평가
    - 라이선스/이용약관: [Microsoft Azure Terms](https://azure.microsoft.com/en-us/support/legal/)
    - 참고: API 이용에는 별도의 요금이 발생할 수 있으며, Microsoft의 정책을 따라야 합니다.

- **OpenAI API**
    - 유형: 유료 API
    - 사용 목적: 사용자 실시간 음성대화 처리
    - 라이선스/이용약관: [OpenAI API Terms of Use](https://openai.com/policies/terms-of-use)
    - 참고: API 이용 시 OpenAI의 정책과 요금제, 사용 제한 조건을 준수해야 합니다.

- **Replicate API**
    - 유형: 유료 API
    - 사용 목적: 혀, 입 모양 매핑 데이터를 기반으로 실시간 입모양, 혀 모양 생성
    - 라이선스/이용약관: [Replicate Terms of Service](https://replicate.com/terms)
    - 참고: 해당 API를 이용할 때 Replicate의 이용약관 및 과금 정책을 반드시 확인하시기 바랍니다.