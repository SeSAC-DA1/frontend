# CarFin AI 추천시스템 설계 문서

## 📋 프로젝트 개요

**목표**: 학술 논문 기반의 검증된 협업 필터링 기술로 중고차 추천시스템 구현
**핵심**: Gemini 멀티 에이전트 + Neural Collaborative Filtering 융합

---

## 🎓 학술적 근거 및 논문 분석

### 1. **Neural Collaborative Filtering (NCF)**
- **논문**: He et al. (2017) "Neural Collaborative Filtering" WWW'17
- **핵심 기여**: Matrix Factorization의 한계를 딥러닝으로 극복
- **CarFin 적용**: 중고차 도메인의 복잡한 사용자-아이템 상호작용 학습

```python
# NCF 핵심 아이디어
user_embedding ⊗ item_embedding → Neural Network → 선호도 예측
```

**중고차 적합성**:
- ✅ 암시적 피드백 (클릭, 찜, 문의) 최적화
- ✅ 희소한 평점 데이터 문제 해결
- ✅ 비선형 사용자 선호도 패턴 학습

### 2. **Wide & Deep Learning**
- **논문**: Cheng et al. (2016) "Wide & Deep Learning for Recommender Systems" Google
- **핵심 아이디어**: 암기(Wide) + 일반화(Deep) 동시 최적화
- **CarFin 적용**: 명확한 규칙 + 복합적 패턴 학습

```
Wide: 가격대 + 브랜드 → 직접적 매칭
Deep: 사용자 임베딩 → 잠재적 선호도 발견
```

**중고차 적합성**:
- ✅ 명시적 조건 (예산, 브랜드) 처리
- ✅ 잠재적 선호도 (디자인, 감성) 학습
- ✅ 콜드 스타트 문제 완화

### 3. **Implicit Feedback Collaborative Filtering**
- **논문**: Hu et al. (2008) "Collaborative Filtering for Implicit Feedback Datasets" ICDM'08
- **핵심 기여**: 암시적 피드백의 확신도(confidence) 모델링
- **CarFin 적용**: 중고차 탐색 행동의 의미 해석

```python
# 확신도 가중치
confidence = 1 + α * frequency
# 중고차: 여러 번 본 차량 = 높은 관심도
```

---

## 🏗 시스템 아키텍처

### **전체 구조**
```
Frontend (Next.js)
├── 사용자 행동 추적
├── 실시간 추천 렌더링
└── A/B 테스트 인터페이스

ML Engine (Python/TensorFlow)
├── Neural Collaborative Filtering
├── Wide & Deep Model
├── Sequential Recommendation
└── Multi-Task Learning

Gemini Multi-Agent
├── Data Collector: 행동 분석
├── Vehicle Expert: 기술적 매칭
├── Finance Expert: 금융 최적화
└── Consultant: 최종 추천 통합
```

### **데이터 플로우**
```
1. 사용자 행동 → 실시간 특성 추출
2. ML 모델 → 후보 차량 생성
3. Gemini Agents → 전문가 검증 및 개선
4. 최종 추천 → UI 렌더링
```

---

## 🔬 구체적 구현 방법론

### **1. Neural Collaborative Filtering 구현**

```python
class CarFinNCF(tf.keras.Model):
    def __init__(self, num_users, num_vehicles, embedding_dim=64):
        super().__init__()

        # 사용자/차량 임베딩
        self.user_embedding = tf.keras.layers.Embedding(num_users, embedding_dim)
        self.vehicle_embedding = tf.keras.layers.Embedding(num_vehicles, embedding_dim)

        # Wide component (선형)
        self.wide_layer = tf.keras.layers.Dense(1, activation='sigmoid')

        # Deep component (MLP)
        self.deep_layers = tf.keras.Sequential([
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])

    def call(self, inputs):
        user_id, vehicle_id, features = inputs

        # 임베딩 조회
        user_emb = self.user_embedding(user_id)
        vehicle_emb = self.vehicle_embedding(vehicle_id)

        # Wide: 선형 조합 (명시적 특성)
        wide_input = tf.concat([user_emb, vehicle_emb, features], axis=1)
        wide_output = self.wide_layer(wide_input)

        # Deep: 비선형 학습 (잠재적 패턴)
        deep_input = tf.concat([user_emb, vehicle_emb], axis=1)
        deep_output = self.deep_layers(deep_input)

        return tf.add(wide_output, deep_output)
```

### **2. 중고차 특화 특성 엔지니어링**

```python
def extract_vehicle_features(vehicle_data, user_profile):
    return {
        # 기본 특성
        'price_ratio': vehicle_data['price'] / user_profile['budget'],
        'age_years': 2024 - vehicle_data['year'],
        'mileage_norm': vehicle_data['mileage'] / 100000,

        # 카테고리 특성
        'brand_match': vehicle_data['brand'] in user_profile['preferred_brands'],
        'size_match': vehicle_data['size'] == user_profile['preferred_size'],
        'fuel_match': vehicle_data['fuel_type'] == user_profile['fuel_preference'],

        # 시간적 특성
        'listing_age_days': (datetime.now() - vehicle_data['listed_date']).days,
        'seasonal_factor': get_seasonal_demand(vehicle_data['type']),

        # 지역적 특성
        'distance_km': calculate_distance(user_profile['location'], vehicle_data['location']),
        'local_popularity': get_local_demand(vehicle_data['location'], vehicle_data['brand'])
    }
```

### **3. Multi-Agent 통합**

```typescript
// lib/multi-agent-recommendation.ts
export class CarFinRecommendationEngine {

    async generateRecommendations(userProfile: UserProfile): Promise<Vehicle[]> {

        // 1단계: ML 모델 기본 추천
        const mlRecommendations = await this.ncfModel.predict({
            userId: userProfile.user_id,
            topK: 50 // 후보군 생성
        });

        // 2단계: Gemini Agents 협업 필터링
        const agentAnalysis = await Promise.all([

            // Data Collector: 행동 패턴 분석
            this.geminiAgent.dataCollector.analyze({
                prompt: `사용자 ${userProfile.user_id}의 최근 30일 차량 탐색 패턴을 분석하여
                        선호하는 차량 타입, 가격대, 브랜드 경향을 파악해주세요.`,
                data: await this.getUserBehaviorData(userProfile.user_id)
            }),

            // Vehicle Expert: 기술적 검증
            this.geminiAgent.vehicleExpert.evaluate({
                prompt: `다음 추천 차량들을 기술적 관점에서 평가해주세요:
                        - 안전성, 신뢰성, 유지비용
                        - 사용자 용도(${userProfile.purpose})에 적합성
                        - 시장 가치 대비 합리성`,
                vehicles: mlRecommendations
            }),

            // Finance Expert: 금융 최적화
            this.geminiAgent.financeExpert.optimize({
                prompt: `사용자 소득(${userProfile.income}만원) 기준으로
                        최적의 구매/할부/리스 옵션을 제안해주세요.`,
                vehicles: mlRecommendations,
                userIncome: userProfile.income
            })
        ]);

        // 3단계: 하이브리드 앙상블
        return this.ensembleRecommendations({
            mlScores: mlRecommendations,
            behaviorInsights: agentAnalysis[0],
            technicalScores: agentAnalysis[1],
            financeOptions: agentAnalysis[2]
        });
    }

    private ensembleRecommendations(inputs: any): Vehicle[] {
        // 가중 평균으로 최종 점수 계산
        const weights = {
            ml: 0.4,        // ML 모델 기본 점수
            technical: 0.3,  // 기술적 적합성
            financial: 0.2,  // 금융 최적화
            behavior: 0.1    // 행동 패턴 보정
        };

        return inputs.mlScores.map(vehicle => ({
            ...vehicle,
            finalScore:
                vehicle.mlScore * weights.ml +
                inputs.technicalScores[vehicle.id] * weights.technical +
                inputs.financeOptions[vehicle.id].score * weights.financial +
                inputs.behaviorInsights.adjustmentScore * weights.behavior,
            explainability: {
                mlReason: vehicle.reason,
                technicalReason: inputs.technicalScores[vehicle.id].reason,
                financialOption: inputs.financeOptions[vehicle.id].bestOption
            }
        })).sort((a, b) => b.finalScore - a.finalScore).slice(0, 10);
    }
}
```

---

## 📊 성능 평가 및 최적화

### **평가 지표**
```python
# 추천 시스템 성능 지표
metrics = {
    'Precision@K': precision_at_k(recommendations, actual_purchases, k=10),
    'Recall@K': recall_at_k(recommendations, actual_purchases, k=10),
    'NDCG@K': ndcg_at_k(recommendations, relevance_scores, k=10),
    'Hit Rate': hit_rate(recommendations, actual_purchases),
    'MRR': mean_reciprocal_rank(recommendations, actual_purchases),

    # 비즈니스 지표
    'CTR': click_through_rate,
    'Conversion Rate': purchase_conversion_rate,
    'Revenue per User': average_revenue_per_user
}
```

### **A/B 테스트 설계**
```typescript
// A/B 테스트 구현
export class RecommendationABTest {

    async getRecommendationStrategy(userId: string): Promise<string> {
        const userSegment = await this.getUserSegment(userId);
        const testGroups = ['ncf_only', 'wide_deep', 'multi_agent_hybrid'];

        return this.assignTestGroup(userId, testGroups, {
            traffic_split: [0.3, 0.3, 0.4], // 하이브리드에 더 많은 트래픽
            segment_weights: userSegment === 'premium' ? [0.2, 0.3, 0.5] : [0.4, 0.3, 0.3]
        });
    }

    async trackConversion(userId: string, recommendationId: string, action: string) {
        await this.analytics.track('recommendation_interaction', {
            user_id: userId,
            recommendation_id: recommendationId,
            action: action, // 'click', 'inquiry', 'test_drive', 'purchase'
            model_version: await this.getModelVersion(userId),
            timestamp: new Date()
        });
    }
}
```

---

## 🚀 구현 로드맵

### **Phase 1: 기반 구축 (4주)**
- [ ] 데이터 수집 파이프라인 구축
- [ ] Neural CF 기본 모델 구현
- [ ] 평가 메트릭 시스템 구축

### **Phase 2: 모델 고도화 (6주)**
- [ ] Wide & Deep 아키텍처 구현
- [ ] Sequential recommendation 추가
- [ ] Multi-task learning 도입

### **Phase 3: 멀티에이전트 통합 (4주)**
- [ ] Gemini Agents 연동
- [ ] 하이브리드 앙상블 시스템
- [ ] 설명 가능한 추천 시스템

### **Phase 4: 프로덕션 최적화 (4주)**
- [ ] 실시간 추론 최적화
- [ ] A/B 테스트 프레임워크
- [ ] 모니터링 및 피드백 루프

---

## 🛠 기술 스택

### **Backend ML**
```yaml
ML Framework: TensorFlow 2.x, PyTorch
Data Processing: pandas, numpy, Apache Spark
Feature Store: Feast, Redis
Model Serving: TensorFlow Serving, FastAPI
Vector DB: Pinecone, ChromaDB
```

### **Frontend**
```yaml
Framework: Next.js 15, TypeScript
UI: Shadcn/UI, Tailwind CSS
State Management: Zustand
Analytics: Mixpanel, Google Analytics
```

### **Infrastructure**
```yaml
Cloud: AWS/GCP
Containers: Docker, Kubernetes
CI/CD: GitHub Actions
Monitoring: Grafana, Prometheus
```

---

## 💡 차별화 포인트

1. **학술적 검증**: 최신 논문 기반의 신뢰성 있는 알고리즘
2. **도메인 특화**: 중고차 시장의 특성을 반영한 커스터마이징
3. **멀티에이전트 융합**: AI 전문가들의 협업으로 추천 품질 향상
4. **설명 가능성**: 사용자가 이해할 수 있는 추천 이유 제공
5. **실시간 최적화**: 지속적 학습을 통한 성능 개선

---

## 📈 예상 성과

- **추천 정확도**: 기존 대비 25-40% 향상
- **사용자 참여도**: CTR 15-25% 증가
- **전환율**: 구매 전환율 10-20% 향상
- **사용자 만족도**: 추천 만족도 30% 이상 증가

이 설계를 바탕으로 CarFin AI는 학술적으로 검증된 최첨단 추천 시스템을 구축할 수 있습니다.