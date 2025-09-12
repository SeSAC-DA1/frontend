# 🚗 CarFin AI - Frontend

AI 기반 개인 맞춤형 차량 추천 플랫폼의 프론트엔드

## 📋 개요

사용자의 선호도와 예산을 분석하여 최적의 중고차를 추천하는 AI 플랫폼

## ⚙️ 요구사항

- **Node.js** 18 이상
- **npm** 또는 **yarn**

## 📁 프로젝트 구조

```
frontend/
├── src/
│   ├── components/          # 재사용 컴포넌트
│   │   ├── VehicleSearch.jsx    # 차량 검색
│   │   └── UserProfile.jsx      # 사용자 프로필
│   ├── App.jsx             # 메인 앱
│   ├── main.jsx           # 진입점
│   └── index.css          # 전역 스타일
├── public/                # 정적 파일
└── package.json          # 의존성 관리
```

## 🎯 현재 상태

### ✅ 완료
- React 19 + Material-UI 기반 UI
- 차량검색/사용자프로필/AI추천 탭 구조
- VehicleSearch, UserProfile 컴포넌트

### 🚧 진행중
- Recommendations 컴포넌트 개발
- Backend API 연동
- 상태 관리 시스템

## 📱 주요 기능

- **차량 검색**: 브랜드, 모델, 가격대별 필터링
- **사용자 프로필**: 개인 선호도 및 예산 입력
- **AI 추천**: 맞춤형 차량 추천 (개발 예정)

## 🛠️ 기술 스택

- **React** 19.1.1
- **Vite** 7.1.2  
- **Material-UI** 7.3.2
- **Axios** 1.11.0
- **ESLint** 9.33.0

## 🚀 실행 방법

```bash
# 의존성 설치
npm install

# 개발 서버 실행 (http://localhost:5173)
npm run dev

# 프로덕션 빌드
npm run build

# 코드 품질 검사
npm run lint
```

## 🎯 개발 계획

**단기 (1-2주)**
- Recommendations 컴포넌트 완성
- API 연동 및 상태관리

**중기 (3-4주)**  
- React Router 도입
- 데이터 시각화
- 성능 최적화

**장기 (1-2개월)**
- TypeScript 도입
- 테스트 코드 작성
- 배포 환경 구축

## 🔗 링크

- [Backend Repository](https://github.com/SeSAC-DA1/backend)
- [API 문서](http://localhost:8000/docs)
- [Issues](https://github.com/SeSAC-DA1/frontend/issues)

---

**SeSAC 데이터 분석 1팀** | **2024년 9월**
