## 조음 훈련 서비스 [말:뻗]
2025 SW중심대학 디지털 경진대회 대상(과학기술정보통신부 장관상) 수상

### 프로젝트 개요
[말:뻗]은 조음 장애로 인해 발음에 어려움을 겪는 사용자를 대상으로, 실시간 음성 분석과 맞춤형 발음 피드백을 제공하는 생성형 AI 기반 조음 훈련 서비스입니다.  
조음 장애인들이 오프라인 치료의 비용적, 시공간적 한계를 극복하고 온라인 환경에서 퀄리티 높은 훈련을 할 수 있도록 합니다.  


<img src="/docs/imgs/thumbnail.png" width="1000">

---

### 데모 웹사이트 링크

- url: [https:malppot.com](https:malppot.com)

---

### 환경

| Part                       | Environment | Version |
|----------------------------|-------------|---------|
| FrontEnd                   | React       | 17.0.2  |
| BackEnd                    | Python      | 3.11.4  |
| WebServer                  | Nginx       | 1.14.2  |
| Publishing Server Hardware | AWS         | EC2     |

---

### 페이지 정보

1. 홈 페이지

   <img src="/docs/imgs/home.png" width="500">

- URL: `/`
- 서비스에 처음 진입하는 메인 화면으로, 로그인 진입점과 주요 메뉴로 이동할 수 있는 라우팅 허브 역할을 합니다.

2. 로그인 페이지

   <img src="/docs/imgs/login.png" width="500">

- URL: `/auth`
- Google 로그인, 외부 인증 수단을 통해 사용자를 인증하고 서비스에 접근할 수 있도록 합니다.

3. AI 말벗 페이지

   <img src="/docs/imgs/ai_malbeot_mode.png" width="500">
   <img src="/docs/imgs/ai_malbeot.png" width="500">

- URL: `/malbeot`
- AI 음성 대화 기능입니다. </br> 상황에 맞게 모드를 이용할 수 있고, 캐릭터와 음성으로 대화하면서 대화에 대한 두려움을 없앨 수 있는 기능입니다. </br>'피드백 모드'에서는 사용자의 발음 데이터를
  기반으로 교정 가이드를 제공합니다. </br> '일반 모드'에서는 자연스러운 일상 대화를 이어가며 사용자 발음 습관을 파악하고, 난이도가 높은 발음이 포함된 문장을 자연스럽게 유도합니다.

4. 말소리 연습실 페이지

   <img src="/docs/imgs/speech.png" width="500">
   <img src="/docs/imgs/speech_result.png" width="500">

- URL: `/speech`
- 사용자가 발음 연습을 진행하는 핵심 페이지로, **문장 입력 → 발화 → 분석 → 피드백**의 흐름을 제공합니다

    1. **문장 입력 및 음성 녹음**
        - 사용자는 원하는 문장을 직접 입력하거나 마이페이지의 추천 단어를 통해 문장을 연습할 수 있습니다.
        - 변환 버튼을 통해 입력한 문장의 **표준 발음**을 확인할 수 있습니다.
        - 마이크 버튼을 눌러 사용자의 음성을 녹음하면 실시간으로 분석이 시작됩니다.
          </br></br>

    2. **입모양 / 혀모양 가이드 제공**
        - 발음해야 하는 음소의 조음 위치를 이해할 수 있도록 **입술, 혀의 움직임을 시각화한 가이드 영상**을 제공합니다.
        - 조음 장애가 있는 사용자도 직관적으로 모방 학습할 수 있도록 구성했습니다.
          </br></br>

    3. **종합 발음 평가**
        - 사용자의 음성을 기준으로 어절 단위로 나누어 계산된 점수와 전체에 대한 **종합 정확도 점수**를 제공합니다.
          </br></br>

    5. **조음 팁 제공**
        - 간단한 조음 팁을 제공합니다.
        - 예: “*ㄱ 발음은 혀 뒷부분을 입천장 뒤쪽에 가볍게 붙인 상태에서 공기를 밀어내듯 내뱉으면 더 정확한 소리가 납니다.*”
          </br></br>

5. 발음 게임 페이지

   <img src="/docs/imgs/game_mode.png" width="500">
   <img src="/docs/imgs/game.png" width="500">

- URL: `/game`
- 간단한 게임을 통해 사용자들이 흥미를 유지하고 꾸준한 재사용으로 이어질 수 있도록 만들었습니다.  
  실제 사용자 테스트 결과 안정된 상황에서는 비교적 정확한 발음을 구사하지만, 실제 대화처럼 약간의 긴장감이 있는 경우 발음이 더욱 어눌해지는 특성을 보였습니다.  
  또한 장애인들의 꾸준한 사용을 유도하기 위해선 흥미요소가 필요하다는 **전문가** 분들의 의견을 참고해 만들었습니다.  
  하늘에서 비처럼 떨어지는 단어를 사용자의 음성으로 맞추어 나가는 게임입니다.

6. 마이 페이지

   <img src="/docs/imgs/mypage.png" width="500">

- URL: `/my`
- 사용자의 발음 기록에 대한 다양한 정보를 확인할 수 있습니다.  
  AI 추천 단어와 사용자에게 나타나는 오류 유형 등을 직관적으로 확인할 수 있습니다.

---

### 팀 소개

| Name | Github                                  | Role   | Major Part  | Minor Part | Tech Stack                              |
|------|-----------------------------------------|--------|-------------|------------|-----------------------------------------|
| 이상벽  | [GitHub](https://github.com/byeok99)    | Leader | Back, Cloud | Front      | FastAPI, Python, AWS, React, Typescript |
| 이연경  | [GitHub](https://github.com/LeeYeonK)   | member | PM          | Design     | React, Typescript                       |
| 차민경  | [GitHub](https://github.com/minkyeongc) | member | Front       | Design     | React, Typescript                       |
