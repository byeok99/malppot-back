src/
│
├── assets/          # 이미지, 폰트, 3D 모델 파일 등 정적 리소스
│   ├── images/
│   ├── models/
│   └── styles/
│
├── components/      # 재사용 가능한 컴포넌트
│   ├── common/      # 버튼, 입력 필드 등 공통 컴포넌트
│   ├── layout/      # 헤더, 푸터 등 레이아웃 관련 컴포넌트
│   └── specific/    # 특정 페이지에 사용되는 독립 컴포넌트
│
├── pages/           # 각 페이지를 구성하는 컴포넌트
│   ├── Home.jsx
│   ├── About.jsx
│   └── Features.jsx
│
├── hooks/           # 커스텀 훅
│   └── use3DModel.js
│
├── services/        # API 호출 관련 코드
│   ├── api.js
│
├── utils/           # 유틸리티 함수
│   ├── helpers.js
│   └── constants.js
│
├── App.jsx          # 메인 애플리케이션
├── index.js         # 진입점
└── routes/          # 라우팅 관련 설정
    └── AppRoutes.jsx
