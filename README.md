# 말:뻗 (Malppot)

조음 장애로 인해 발음 연습이 필요한 사용자를 위한 AI 기반 조음 훈련 서비스입니다. 사용자가 문장을 입력하고 말하면 표준 발음 변환, 음성 평가, 음절별 입모양·혀모양 가이드, AI 조음 팁, 누적 발음 리포트까지 하나의 학습 흐름으로 연결합니다.

2025 SW중심대학 디지털 경진대회 대상(과학기술정보통신부 장관상) 및 인기상 수상 프로젝트입니다.

```text
입장 → Google 로그인 → AI 말벗 / 말소리 연습실 / 발음 게임 → 음성 평가 → 발음 기록 저장 → 마이페이지 리포트·추천 단어
```

<img src="/docs/imgs/thumbnail.png" width="1000">

## 핵심 기능

- Google OAuth 기반 로그인과 JWT access token / refresh token 인증
- 한국어 문장 입력 후 G2P 기반 표준 발음 변환
- Azure Speech Pronunciation Assessment 기반 어절·음소 단위 발음 평가
- 음절별 혀모양·입모양 가이드 영상과 GPT 조음 팁 제공
- OpenAI Realtime API 기반 AI 말벗 음성 대화
- 사용자 발음 기록을 반영한 피드백 모드와 자유 대화 모드
- 하늘에서 떨어지는 단어를 음성으로 맞추는 발음 게임
- 스테이지 클리어, 무한 모드 최고 점수, 발음 기록 저장
- 마이페이지 발음 지도, 최근 정확도 추이, 자음별 상세 리포트, AI 추천 단어
- 환자용 PDF 리포트 생성을 위한 분석 데이터 API

## 기술 스택

| 영역 | 기술 | 활용 목적 |
| --- | --- | --- |
| Frontend | React 19, TypeScript, Vite | 컴포넌트 기반 SPA와 빠른 개발 서버/번들링 |
| Frontend 상태/라우팅 | Redux Toolkit, React Query, React Router | 인증 토큰, 서버 상태 캐싱, 페이지 전환 관리 |
| Frontend 음성 | Web Speech API, AudioWorklet, WebSocket | 게임 음성 입력과 AI 말벗 실시간 오디오 송수신 |
| Frontend 리포트 | html2pdf.js, styled-components | 발음 리포트 UI와 PDF 생성 |
| Backend | Python 3.11, FastAPI | REST API, WebSocket, Swagger 문서 자동화 |
| Backend DI | dependency-injector | 설정, DB 세션, 도메인 서비스 조립 |
| Backend 영속성 | SQLAlchemy, MySQL | 사용자, 발음 기록, 게임 진행, 추천 단어 저장 |
| 인증 | Google OAuth, PyJWT, HttpOnly refresh cookie | 외부 로그인과 access token 재발급 |
| 음성 평가 | Azure Cognitive Services Speech SDK | 한국어 발음 정확도, 유창성, 완전성 평가 |
| AI 대화 | OpenAI Realtime API | 실시간 음성 대화와 발음 피드백 모드 |
| AI 텍스트 | OpenAI Chat Completions | 음절별 조음 팁과 추천 단어 생성 |
| 영상 생성 | Replicate Frame Interpolation | 입모양·혀모양 전환 영상 생성 |
| 배포 | AWS EC2, Nginx | 백엔드 런타임과 웹 서비스 배포 |

## 전체 아키텍처

```text
React SPA
  ├─ Home / Auth / AI 말벗 / 말소리 연습실 / 발음 게임 / 마이페이지
  ├─ ApiClient(Axios) + React Query + Redux auth state
  └─ WebSocket + AudioWorklet

FastAPI
  ├─ auth        Google OAuth, JWT, refresh token
  ├─ speech      G2P 변환, Azure 발음 평가, 음절 가이드 캐시
  ├─ malbeot     OpenAI Realtime 음성 대화
  ├─ game        스테이지, 무한 모드, 게임 평가 저장
  ├─ mypage      발음 통계, 리포트, 추천 단어 조회
  └─ common/di   dependency, error, config, service wiring

External APIs
  ├─ Google OAuth
  ├─ Azure Speech
  ├─ OpenAI
  └─ Replicate

MySQL
  ├─ users, practice_sessions, practice_words, pronunciation_scores
  ├─ syllables, jamo_statistics, recommendation_words
  └─ stage_info, game_words, user_stage_progress, endless_scores
```

백엔드는 도메인별로 `controller / service / schema`를 분리합니다. Controller는 HTTP·WebSocket 입출력과 dependency 조립을 맡고, Service는 G2P 변환, 외부 API 호출, 평가 결과 매핑, DB 저장, 통계 갱신 같은 유스케이스를 처리합니다.

## Frontend 데이터 흐름

프런트는 페이지 컴포넌트가 직접 `axios`를 다루지 않고, 도메인별 API 모듈과 hook을 통해 서버 상태를 가져옵니다. Access token은 Redux 상태에 보관하고, 요청 interceptor가 `Authorization` 헤더를 붙입니다. 401 응답이 오면 refresh token cookie로 access token을 재발급한 뒤 원 요청을 재시도합니다.

```text
View 이벤트
→ hook / page handler
→ domain API module
→ ApiClient(Axios)
→ FastAPI JSON·multipart·WebSocket
→ 응답 DTO
→ React Query cache 또는 local state
→ 화면 렌더링
```

### 주요 화면 흐름

1. **홈**: `/`에서 AI 말벗, 말소리 연습실, 발음 게임으로 진입한다.
2. **로그인**: `/auth`에서 Google authorization code를 받아 `POST /auth/login`으로 전달한다. 서버는 사용자 정보를 저장하고 access token과 refresh cookie를 반환한다.
3. **AI 말벗**: `/malbeot`에서 피드백 모드 또는 일반 모드를 고른 뒤 `WebSocket /malbeot/ws`로 OpenAI Realtime 음성 대화를 시작한다.
4. **말소리 연습실**: `/speech`에서 문장을 입력해 `POST /speech/convert`로 표준 발음을 확인하고, 녹음 파일을 `POST /speech/evaluate`로 보내 발음 평가를 받는다.
5. **발음 게임**: `/game`에서 스테이지 또는 무한 모드를 선택한다. 게임 중 인식된 단어는 `POST /game/evaluate/bulk`로 평가하고, 클리어·최고 점수는 별도 API로 저장한다.
6. **마이페이지**: `/my`에서 `GET /mypage/summary`, `GET /mypage/phoneme/{jamo}`, `GET /mypage/report`를 통해 발음 지도, 추천 단어, 상세 리포트를 표시한다.

## Backend 데이터 흐름

### 1. 인증

```text
POST /auth/login
→ Google token endpoint에 authorization code 교환
→ Google userinfo 조회
→ users 조회 또는 신규 등록
→ JWT access token 발급
→ refresh token을 HttpOnly cookie로 저장
```

후속 REST 요청은 `Authorization: Bearer <access_token>` 헤더를 사용합니다. WebSocket 기반 AI 말벗은 브라우저 제약을 고려해 query string의 `access_token`을 검증합니다.

### 2. 문장 변환과 음절 가이드 캐시

```text
POST /speech/convert
→ KoG2Padvanced로 표준 발음 변환
→ 변환 문장의 음절 추출
→ syllables 캐시 조회
→ 누락된 tongue/lips 가이드 비동기 생성
→ converted_text 반환
```

`syllables`는 한글 음절을 key로 혀모양 URL, 입모양 URL, GPT 조음 팁을 저장합니다. 같은 음절 요청이 동시에 들어와도 기본 행을 먼저 보장하고 음절별 lock으로 중복 insert와 누락 컬럼 문제를 줄입니다.

### 3. 발음 평가와 기록 저장

```text
POST /speech/evaluate
→ 업로드 음성을 wav로 변환
→ Azure Pronunciation Assessment 실행
→ 단어·음소 점수와 오류 유형 파싱
→ PracticeSession 저장
→ PracticeWord / PronunciationScore 저장
→ JamoStatistic과 users 요약 통계 갱신
→ 단어별 피드백 반환
```

Azure 결과는 서비스 내부에서 말뭉치 단어와 다시 매핑됩니다. 프런트는 반환된 단어별 `syllables` 데이터를 이용해 음절 가이드 영상과 AI 조음 팁을 함께 보여줍니다.

### 4. AI 말벗

```text
WebSocket /malbeot/ws?mode=feedback|general
→ access token으로 사용자 인증
→ mode별 시스템 프롬프트 생성
→ feedback 모드는 마이페이지의 취약 자음 조회
→ OpenAI Realtime 세션 연결
→ 브라우저 오디오와 모델 음성/텍스트 이벤트 중계
```

피드백 모드는 사용자의 누적 발음 기록에서 주의해야 할 자음을 찾아 해당 발음이 포함된 문장 연습을 유도합니다. 일반 모드는 직접적인 교정보다 자연스러운 대화를 통해 발화 자신감을 높이는 방향으로 동작합니다.

### 5. 발음 게임

```text
GET /game/stages
→ stage_info + game_words 조회
→ 스테이지별 단어, 속도, 목표 점수 반환

POST /game/evaluate/bulk
→ 게임 중 맞춘 단어만 필터링
→ Azure 평가
→ PracticeSession / PracticeWord 저장
→ 사용자 통계 갱신

POST /game/clear, POST /game/endless
→ 스테이지 클리어와 무한 모드 최고 점수 저장
```

게임 기록도 일반 발음 연습과 같은 통계 테이블에 반영되므로, 마이페이지 리포트와 AI 말벗 피드백에 다시 활용됩니다.

### 6. 마이페이지 리포트

```text
GET /mypage/summary
→ users 요약 컬럼 + jamo_statistics + 최근 7일 평균 조회

GET /mypage/phoneme/{jamo}
→ 특정 자음의 위치별 정확도·오류 경향·추천 단어·연습 기록 조회

GET /mypage/report
→ 환자용 리포트에 필요한 전체 통계 반환
```

`jamo_statistics`는 자음별 시도 수와 누적 점수를 저장해 반복 계산을 줄입니다. `users`에는 전체 연습 횟수, 연속 연습일, 현재/이전 평균 정확도를 반정규화해 빠르게 조회합니다.

## 세션·동시성·안전성

| 항목 | 설계 |
| --- | --- |
| 인증 세션 | access token은 메모리/Redux 상태, refresh token은 HttpOnly cookie로 관리 |
| REST 인증 | `Authorization` 헤더를 dependency에서 검증하고 사용자 엔티티를 주입 |
| WebSocket 인증 | `access_token` query parameter를 검증해 AI 말벗 세션 시작 |
| 음절 캐시 | `syllables.syllable_char`를 primary key로 사용 |
| 음절 동시성 | 음절별 `asyncio.Lock`과 선행 row 보장으로 중복 insert와 누락 필드 방지 |
| 외부 API 비용 절감 | tongue/lips/GPT 데이터가 이미 있으면 외부 생성 호출 생략 |
| 게임 점수 저장 | MySQL `ON DUPLICATE KEY UPDATE`로 무한 모드 최고 점수 갱신 |
| 비밀 관리 | Google, JWT, OpenAI, Azure, Replicate 키는 설정 파일 또는 환경변수로 주입 |
| 오류 처리 | 도메인별 CustomException을 FastAPI exception handler에서 일관된 JSON으로 변환 |

## 데이터 모델

| 테이블 | 역할 |
| --- | --- |
| `users` | Google 로그인 사용자, 프로필, 연습 요약 통계 |
| `practice_sessions` | 문장 단위 발음 연습 세션과 전체 점수 |
| `practice_words` | 세션 안의 단어별 발화 기록과 평균 점수 |
| `pronunciation_scores` | 단어 안의 자모별 점수와 초성/종성 위치 |
| `syllables` | 음절별 tongue/lips 가이드 URL과 GPT 조음 팁 캐시 |
| `jamo_statistics` | 사용자별 자음 시도 수와 누적 점수 |
| `recommendation_words` | 자음별 AI 추천 단어와 예문 |
| `stage_info` | 게임 스테이지 난이도, 목표 점수, 속도, 생명 수 |
| `game_words` | 게임에 출제되는 단어와 이미지 |
| `stage_words_link` | 스테이지와 단어의 다대다 연결 |
| `user_stage_progress` | 사용자별 스테이지 클리어 기록 |
| `endless_scores` | 무한 모드 최고 점수 |

## 실행 방법

프런트엔드:

```bash
cd front/malppot
npm install
npm run dev
```

백엔드:

```bash
cd back
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r malppot/requirements.txt
python -m uvicorn malppot.main:app --reload
```

환경 설정은 `back/malppot/example.config.yaml`을 참고해 DB, JWT, Google OAuth, OpenAI, Azure Speech, Replicate 값을 준비합니다. 실제 키와 비밀번호가 포함된 파일은 커밋하지 않습니다.

## 화면

| 홈 | 로그인 |
| --- | --- |
| <img src="/docs/imgs/home.png" width="420"> | <img src="/docs/imgs/login.png" width="420"> |

| AI 말벗 | 말소리 연습실 |
| --- | --- |
| <img src="/docs/imgs/ai_malbeot.png" width="420"> | <img src="/docs/imgs/speech_result.png" width="420"> |

| 발음 게임 | 마이페이지 |
| --- | --- |
| <img src="/docs/imgs/game.png" width="420"> | <img src="/docs/imgs/mypage.png" width="420"> |

## 팀

| Name | Github | Role | Major Part | Minor Part | Tech Stack |
| --- | --- | --- | --- | --- | --- |
| 이상벽 | [GitHub](https://github.com/byeok99) | Leader | Back, Cloud | Front | FastAPI, Python, AWS, React, TypeScript |
| 이연경 | [GitHub](https://github.com/LeeYeonK) | Member | PM | Design | React, TypeScript |
| 차민경 | [GitHub](https://github.com/minkyeongc) | Member | Front | Design | React, TypeScript |
