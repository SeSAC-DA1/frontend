# 🚗 CarFin AI - 논문 기반 차량 추천 시스템

## 📋 프로젝트 개요

**CarFin AI**는 학술 논문 기반의 하이브리드 차량 추천 시스템입니다. Gemini 멀티에이전트와 최신 딥러닝 추천 알고리즘을 결합하여 개인 맞춤형 차량 추천 및 금융 상담 서비스를 제공합니다.

### 🎯 핵심 특징
- **📚 5개 학술 논문 기반 추천 알고리즘**
- **🤖 Gemini 3개 AI 에이전트** (vehicle_expert, finance_expert, consultant)
- **🧠 Keras 기반 커스텀 딥러닝 모델**
- **⚡ 실시간 하이브리드 추천**
- **📊 A/B 테스트 및 성능 최적화**

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js 15    │    │   FastAPI       │    │  Recommendation │
│   Frontend      │◄──►│   Backend       │◄──►│     Engine      │
│                 │    │                 │    │                 │
│ • 차량 검색     │    │ • API 서빙      │    │ • 5개 알고리즘  │
│ • 추천 결과     │    │ • 에이전트 관리 │    │ • 앙상블 학습   │
│ • 사용자 추적   │    │ • 데이터 처리   │    │ • 실시간 추론   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────►│  PostgreSQL     │◄─────────────┘
                        │  Database       │
                        │                 │
                        │ • 사용자 데이터 │
                        │ • 차량 정보     │
                        │ • 상호작용 로그 │
                        └─────────────────┘
```

---

## 🧠 논문 기반 추천 알고리즘

### 📚 구현된 학술 논문

| 논문 | 알고리즘 | 구현 상태 | 우선순위 | 특징 |
|------|----------|----------|----------|------|
| **Neural Collaborative Filtering** (He et al. 2017) | NCF | ✅ **구현완료** | 🥇 **핵심** | GMF + MLP 하이브리드 |
| **Matrix Factorization** (Koren, 2009) | SVD | 🔄 **구현중** | 🥈 **보조** | 협업필터링 기본 |
| **Wide & Deep Learning** (Cheng et al. 2016) | Wide&Deep | 📋 **계획됨** | 🥉 **확장** | 메모리제이션 + 일반화 |
| **DeepFM** (Guo et al. 2017) | DeepFM | 📋 **계획됨** | 🥉 **확장** | FM + DNN 결합 |
| **BPR** (Rendle et al. 2009) | BPR | 📋 **계획됨** | 🥉 **확장** | 암시적 피드백 |

### 🎯 단계별 구현 전략
```python
# Phase 1: NCF 중심 (현재)
primary_model = {
    'ncf': 1.0,                    # Neural CF 100% 비중
    'fallback_mock': 'available'   # Mock 시스템 백업
}

# Phase 2: 하이브리드 (목표)
ensemble_weights = {
    'neural_cf': 0.50,             # 딥러닝 핵심
    'matrix_factorization': 0.30,  # 전통적 CF
    'wide_deep': 0.20              # 하이브리드 확장
}

# Phase 3: 완전 앙상블 (최종)
full_ensemble = {
    'neural_cf': 0.35, 'matrix_factorization': 0.25,
    'wide_deep': 0.20, 'deepfm': 0.15, 'bpr': 0.05
}
```

---

## 🛠️ 기술 스택

### Backend (Python)
```toml
# 🎯 Core FastAPI + Multi-Agent AI
fastapi = ">=0.116.1"
google-genai = ">=1.37.0"
crewai = ">=0.186.1"

# 🧠 논문 기반 추천시스템 (PyCaret 제거)
tensorflow = ">=2.17.0"           # Keras 포함
tensorflow-recommenders = ">=0.7.3"
scikit-surprise = ">=1.1.3"      # Matrix Factorization
lightfm = ">=1.17"               # Hybrid CF+Content
implicit = ">=0.7.2"             # BPR, Fast ALS

# 📊 데이터 처리
numpy = ">=2.3.3"
pandas = ">=2.3.2"
scikit-learn = ">=1.7.2"
```

### Frontend (TypeScript)
```json
{
  "next": "15.5.3",
  "react": "19.0.0",
  "typescript": "5.7.2",
  "tailwindcss": "3.4.1",
  "@shadcn/ui": "latest"
}
```

### Database
- **PostgreSQL**: 사용자, 차량, 평점 데이터
- **Redis** (예정): 추천 결과 캐싱

---

## 📡 API 통합 아키텍처

### 1. Next.js → FastAPI 통합

```typescript
// carfin-ui/src/app/api/recommendations/route.ts
export async function POST(request: NextRequest) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  try {
    // Enhanced FastAPI 백엔드 호출
    const response = await fetch(`${apiUrl}/api/recommendations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_profile: {
          user_id: userId,
          age: userProfile.age,
          income: userProfile.income,
          preferences: userProfile.preferences,
          budget_range: userProfile.budgetRange
        },
        recommendation_type: 'academic_hybrid',
        limit: 12
      })
    });

    const recommendations = await response.json();

    // A/B 테스트 메트릭 기록
    experimentManager.recordMetric('algorithm_comparison_v1', userId, 'impression');

    return NextResponse.json(recommendations);

  } catch (error) {
    // Fallback to mock engine
    return mockRecommendationEngine.getRecommendations(request);
  }
}
```

### 2. FastAPI 추천 서빙

```python
# academic_recommendation_fastapi.py
from academic_recommendation_system import get_academic_system

@app.post("/api/recommendations")
async def get_academic_recommendations(request: RecommendationRequest):
    """논문 기반 하이브리드 추천 API"""
    start_time = datetime.now()

    try:
        # Academic 추천 엔진 로드
        system = get_academic_system()

        # 사용자 프로필 변환
        user_dict = {
            "user_id": request.user_profile.user_id,
            "age": request.user_profile.age,
            "income": request.user_profile.income,
            "preferences": request.user_profile.preferences,
            "budget_max": request.user_profile.budget_range.get("max", 5000)
        }

        # 5개 논문 알고리즘 실행 + 앙상블
        academic_results = system.get_academic_recommendations(
            user_dict,
            n_recommendations=request.limit
        )

        # 최종 추천 결과 (앙상블)
        final_recommendations = academic_results['ensemble']

        # 처리 시간 계산
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return RecommendationResponse(
            recommendations=[
                VehicleRecommendation(
                    vehicle_id=str(rec['car_id']),
                    score=rec['score'],
                    rank=i + 1,
                    reasons=rec['papers'],  # 논문 기반 이유
                    confidence=rec['confidence'],
                    algorithm=rec['algorithm']
                ) for i, rec in enumerate(final_recommendations)
            ],
            metadata={
                "algorithm": "Academic Ensemble (5 Papers)",
                "papers": ["Koren 2009", "He et al. 2017", "Cheng et al. 2016", "Guo et al. 2017", "Rendle et al. 2009"],
                "models_used": list(academic_results.keys()),
                "processing_time_ms": int(processing_time)
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Academic recommendation failed: {str(e)}")
```

### 3. Gemini 멀티에이전트 통합

```python
# agents/crew_setup.py
class CarFinAgents:
    def __init__(self):
        self.recommendation_engine = get_academic_system()  # 논문 기반 엔진

        # 3개 Gemini 에이전트
        self.vehicle_expert = Agent(
            role="차량 전문가",
            goal="차량 특성 분석 및 매칭",
            llm=ChatGoogleGenerativeAI(model="gemini-pro")
        )

        self.finance_expert = Agent(
            role="금융 전문가",
            goal="최적 금융 상품 추천",
            llm=ChatGoogleGenerativeAI(model="gemini-pro")
        )

        self.consultant = Agent(
            role="AI 상담사",
            goal="종합 상담 및 최종 추천",
            llm=ChatGoogleGenerativeAI(model="gemini-pro")
        )

    def get_vehicle_recommendations(self, user_query: str):
        """에이전트 + 학술 추천 결합"""

        # 1. 학술 추천 엔진 결과
        academic_recs = self.recommendation_engine.get_academic_recommendations(
            self._parse_user_query(user_query)
        )

        # 2. 에이전트 분석
        agent_analysis = self.crew.kickoff({
            'user_query': user_query,
            'academic_recommendations': academic_recs,
            'context': 'hybrid_recommendation'
        })

        return {
            'academic_recommendations': academic_recs,
            'agent_response': agent_analysis,
            'status': 'success'
        }
```

---

## 🚀 서비스 연동 플로우

### 1. 사용자 상호작용
```
사용자 입력 → Next.js UI → API Route → FastAPI → Academic Engine
     ↓              ↓           ↓         ↓            ↓
 버튼 클릭 → 차량 그리드 → 추천 API → 논문 알고리즘 → 5개 결과
     ↓              ↓           ↓         ↓            ↓
 행동 추적 → 분석 대시보드 → A/B 테스트 → 성능 평가 → 모델 개선
```

### 2. 실시간 추천 파이프라인
```python
# 실시간 추천 흐름
def real_time_recommendation_pipeline(user_id: str, context: dict):
    # Phase 1: 빠른 후보 생성 (Matrix Factorization)
    quick_candidates = surprise_model.predict_top_k(user_id, k=50)

    # Phase 2: 딥러닝 재랭킹 (Neural CF + DeepFM)
    reranked = neural_models.rerank(quick_candidates, user_features)

    # Phase 3: 비즈니스 규칙 적용 (재고, 지역, 예산)
    filtered = apply_business_rules(reranked, context)

    # Phase 4: 최종 다양성 최적화
    final_recs = diversify_recommendations(filtered, diversity_lambda=0.3)

    return final_recs[:12]  # Top 12 추천
```

---

## 📊 성능 및 모니터링

### A/B 테스트 설정
```typescript
// A/B 테스트 변형
const experiments = {
  'algorithm_comparison_v1': {
    'control': 'matrix_factorization_only',
    'ncf': 'neural_collaborative_filtering',
    'wide_deep': 'wide_and_deep_learning',
    'ensemble': 'academic_ensemble'  // 권장
  }
}

// 성능 메트릭 추적
experimentManager.recordMetric(experimentId, userId, 'impression', 12);
experimentManager.recordMetric(experimentId, userId, 'click', 3);
experimentManager.recordMetric(experimentId, userId, 'conversion', 1);
```

### 예상 성능 지표
```yaml
Matrix Factorization (Baseline):
  RMSE: ~1.2
  MAE: ~0.9
  추론 속도: ~50ms

Neural CF (목표):
  RMSE: ~1.0
  MAE: ~0.7
  추론 속도: ~100ms

Academic Ensemble (최종):
  RMSE: ~0.9
  MAE: ~0.6
  추론 속도: ~150ms
  정확도 향상: ~25%
```

---

## 🔧 환경 설정

### 1. Backend 실행
```bash
# 의존성 설치
pip install -r pyproject.toml

# 환경 변수 설정
export DATABASE_URL="postgresql://user:pass@localhost:5432/carfin"
export GOOGLE_API_KEY="your-gemini-api-key"

# FastAPI 서버 시작
uvicorn academic_recommendation_fastapi:app --host 0.0.0.0 --port 8000
```

### 2. Frontend 실행
```bash
cd carfin-ui

# 의존성 설치
npm install

# 환경 변수 설정
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Next.js 개발 서버
npm run dev
```

### 3. 데이터베이스 설정
```sql
-- PostgreSQL 테이블 생성
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    age INTEGER,
    income INTEGER,
    preferences JSONB
);

CREATE TABLE cars (
    id SERIAL PRIMARY KEY,
    make VARCHAR(50),
    model VARCHAR(100),
    year INTEGER,
    price INTEGER,
    category VARCHAR(50),
    features JSONB
);

CREATE TABLE user_ratings (
    user_id INTEGER REFERENCES users(id),
    car_id INTEGER REFERENCES cars(id),
    rating DECIMAL(2,1),
    timestamp TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, car_id)
);
```

---

## 📈 다음 단계 우선순위

### 1. 즉시 실행 (1주)
- [x] PyCaret 제거 및 학술 라이브러리 전환
- [x] Keras 기반 Neural CF 구현
- [ ] FastAPI 엔드포인트 통합 테스트
- [ ] Next.js 프론트엔드 연동 검증

### 2. 단기 목표 (2-4주)
- [ ] 실제 차량 데이터 크롤링 및 전처리
- [ ] PostgreSQL 연동 및 사용자 추적 시스템
- [ ] A/B 테스트 결과 분석 대시보드
- [ ] 추천 성능 최적화 (캐싱, 배치 예측)

### 3. 중기 목표 (1-3개월)
- [ ] 실시간 학습 파이프라인 구축
- [ ] 추천 설명 가능성 (Explainable AI)
- [ ] 모바일 앱 연동
- [ ] 프로덕션 배포 (Docker + Kubernetes)

---

## 🤝 기여자

- **Lead Developer**: 논문 기반 추천 시스템 설계 및 구현
- **AI Researcher**: 5개 학술 논문 알고리즘 최적화
- **Frontend Developer**: Next.js 15 + Shadcn/UI 구현
- **Data Engineer**: PostgreSQL + 실시간 파이프라인

---

## 📝 라이선스

MIT License - 학술 목적 및 상업적 사용 가능

---

## 📞 문의

- **이슈 트래킹**: GitHub Issues
- **기술 문의**: academic.carfin.ai@email.com
- **비즈니스 문의**: business@carfin.ai

---

*🎓 "세계 수준의 학술 논문 기반 차량 추천 시스템" - CarFin AI Team*