# CarFinanceAI 실제 데이터 통합 계획

## 📈 단계별 데이터 개선 로드맵

### Phase 1: 현재 시뮬레이션 데이터 검증 (완료)
- ✅ 고품질 시뮬레이션 데이터셋 생성
- ✅ NCF 알고리즘 구현 및 검증
- ✅ 웹서비스 통합 테스트
- **목표**: NCF 논문 기반 추천 시스템의 유효성 입증

### Phase 2: 실제 차량 데이터 확보 (즉시 실행 가능)
**수집 가능한 공개 데이터:**
```python
# 1. Kaggle 자동차 데이터셋
- "Car Features and MSRP" (40,000+ 차량)
- "Used Cars Dataset" (50,000+ 중고차 매물)
- "Automotive Dataset" (연비, 성능 데이터)

# 2. 정부 공개 데이터 (data.go.kr)
- 자동차 등록 현황 통계
- 연식별/브랜드별 등록 대수
- 지역별 자동차 분포

# 3. 엔카 공개 API/크롤링 (합법적 범위)
- 차량 기본 정보 (브랜드, 모델, 가격)
- 지역별 매물 분포
- 인기 차량 랭킹
```

### Phase 3: 하이브리드 데이터 구축 (2-4주)
```python
# 실제 차량 정보 + 시뮬레이션 사용자 행동
real_vehicles = load_kaggle_car_dataset()  # 실제 차량 50,000대
simulated_users = generate_realistic_users()  # 시뮬레이션 사용자 1,000명
hybrid_interactions = generate_behavior_patterns(
    real_vehicles, simulated_users,
    pattern_source="real_market_trends"
)
```

### Phase 4: 실제 사용자 데이터 수집 (서비스 출시 후)
```python
# 웹서비스 출시 후 실제 사용자 행동 수집
user_clicks = track_vehicle_clicks()
user_searches = track_search_patterns()
user_inquiries = track_inquiry_data()

# 실시간 모델 업데이트
ncf_model.incremental_train(new_interactions)
```

## 🎯 즉시 실행 가능한 데이터 소스

### 1. Kaggle 데이터셋 (무료, 즉시 다운로드)
```bash
# Kaggle CLI 설치 및 데이터 다운로드
pip install kaggle
kaggle datasets download -d austinreese/craigslist-carstrucks-data
kaggle datasets download -d doaaalsenani/usa-cers-dataset
```

### 2. 정부 공개 데이터 (data.go.kr)
```python
# 자동차 등록 현황 API
api_url = "https://www.data.go.kr/iim/api/selectAPIAcountView.do"
params = {
    "publicDataPk": "15013115",  # 자동차 등록 현황
    "serviceKey": "your_api_key"
}
```

### 3. 크롤링 가능한 공개 정보
```python
# robots.txt 준수 하에 수집 가능한 데이터
- 엔카/SK엔카 차량 목록 (가격, 기본정보만)
- 다나와 자동차 리뷰 (평점, 후기)
- 자동차 커뮤니티 인기글/조회수
```

## 📊 데이터 품질 개선 계획

### 현재 데이터셋 보강
```python
# 1. 실제 시장 가격 반영
real_price_data = fetch_market_prices()
update_vehicle_pricing(current_dataset, real_price_data)

# 2. 지역별 선호도 패턴 추가
regional_patterns = analyze_regional_preferences()
enhance_user_behavior(current_dataset, regional_patterns)

# 3. 계절성/트렌드 반영
seasonal_trends = get_automotive_trends()
add_temporal_patterns(current_dataset, seasonal_trends)
```

### NCF 성능 검증 기준
```python
# 현재 시뮬레이션 데이터로도 검증 가능한 메트릭
metrics = {
    'precision_at_k': [1, 5, 10],
    'recall_at_k': [1, 5, 10],
    'ndcg_at_k': [1, 5, 10],
    'hit_ratio': [1, 5, 10],
    'coverage': 'item_coverage',
    'diversity': 'intra_list_diversity'
}
```

## 🚀 실행 우선순위

### 🟢 즉시 실행 (현재 주)
1. **현재 시뮬레이션 데이터로 NCF 시스템 완성**
2. **웹서비스 통합 및 실제 테스트**
3. **NCF vs 기본 추천 성능 비교**

### 🟡 단기 목표 (2-4주)
1. **Kaggle 차량 데이터셋 통합**
2. **정부 공개 데이터 활용**
3. **하이브리드 데이터셋 구축**

### 🔵 장기 계획 (2-6개월)
1. **실제 사용자 행동 데이터 수집**
2. **실시간 모델 업데이트 시스템**
3. **A/B 테스트 기반 성능 개선**

## 💡 결론

**현재 시뮬레이션 데이터도 NCF 검증에는 충분히 유효합니다!**

- MovieLens, Amazon Product Reviews도 특정 도메인 데이터
- 중요한 것은 **추천 알고리즘의 상대적 성능 개선**
- 실제 데이터는 **점진적으로 품질을 향상**시키는 방향으로 접근

**즉시 우선순위: 현재 데이터로 NCF 시스템을 완성하고 웹서비스와 통합하여 실제 작동하는 추천 엔진을 만드는 것!**