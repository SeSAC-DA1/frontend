# CarFin AI 멀티에이전트 차량 추천 시스템 📁

## 🚗 프로젝트 개요
CrewAI 기반 멀티에이전트 시스템으로 개인화된 차량 추천과 금융 상담을 제공하는 AI 서비스입니다.

## 📂 폴더 구조

### 🔧 backend/
**FastAPI 백엔드 서버**
- `simple_main.py`: 메인 서버 파일 (포트 8000)
  - RESTful API 엔드포인트 제공
  - 멀티에이전트 시스템과 연동
  - 사용자 관리, 채팅, 추천, 금융 상담 API

### 🤖 agents/
**CrewAI 멀티에이전트 시스템**
- `crew_setup.py`: AI 에이전트 설정 및 관리
  - 차량 추천 전문가 에이전트
  - 자동차 금융 상담 전문가 에이전트
  - OpenAI GPT-5 통합
  - PyCaret ML 엔진 연동

### 🧠 ml_engine/
**PyCaret 기반 머신러닝 추천 엔진**
- `recommendation_engine.py`: ML 추천 시스템
  - 협업 필터링 기반 개인화 추천
  - 사용자 프로필 분석
  - 차량 데이터 처리 및 훈련

### 📊 data_crawler/
**데이터 수집 및 처리**
- `encar_crawler.py`: 엔카 차량 데이터 크롤러
- `encar_sample_data.py`: 샘플 데이터 생성
- `aws_encar_crawler.py`: AWS 기반 크롤러

## 🔧 의존성
- `pyproject.toml`: Python 패키지 의존성 관리
  - FastAPI, CrewAI, PyCaret, OpenAI, SQLAlchemy 등

## 🚀 실행 방법

### 1. 의존성 설치
```bash
# uv를 사용한 패키지 설치
uv sync
```

### 2. 환경 변수 설정
```bash
export OPENAI_API_KEY="your_openai_api_key"
export DATABASE_URL="your_database_url"
```

### 3. 서버 실행
```bash
# 백엔드 서버 시작
python backend/simple_main.py
```

## 🔄 시스템 흐름

1. **사용자 입력** → FastAPI 서버 (`simple_main.py`)
2. **AI 에이전트 처리** → CrewAI 시스템 (`crew_setup.py`)
3. **ML 분석** → PyCaret 추천 엔진 (`recommendation_engine.py`)
4. **데이터 소스** → 엔카 크롤러 (`data_crawler/`)

## 🎯 주요 기능

- **개인화 차량 추천**: 사용자 선호도 기반 ML 추천
- **AI 금융 상담**: 대출/리스/할부 옵션 분석
- **실시간 채팅**: 멀티에이전트와 자연스러운 대화
- **하이브리드 UI**: 빠른 입력 + 채팅 인터페이스

## 📞 API 엔드포인트

- `POST /api/chat`: AI 에이전트 채팅 상담
- `POST /api/recommend`: 차량 추천 요청
- `POST /api/finance`: 금융 옵션 계산
- `GET /health`: 시스템 상태 확인

---
**개발 완료**: 2025년 9월 16일  
**기술 스택**: Python, FastAPI, CrewAI, PyCaret, OpenAI GPT-5