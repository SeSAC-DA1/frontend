-- CarFinanceAI 데이터베이스 스키마
-- 실제 추천시스템을 위한 최적화된 테이블 구조

-- 1. 사용자 테이블
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    age INTEGER,
    gender VARCHAR(10) CHECK (gender IN ('male', 'female', 'other')),
    location VARCHAR(100),
    income_range VARCHAR(50), -- '3000-5000', '5000-7000' etc.
    occupation VARCHAR(100),
    family_size INTEGER DEFAULT 1,
    driving_experience INTEGER, -- 운전 경력 (년)

    -- 추천 시스템용 선호도 필드
    preferred_brands TEXT[], -- ['현대', 'BMW', '기아']
    preferred_fuel_type VARCHAR(50), -- 'gasoline', 'hybrid', 'electric'
    budget_min INTEGER, -- 최소 예산 (만원)
    budget_max INTEGER, -- 최대 예산 (만원)
    preferred_body_type VARCHAR(50), -- 'sedan', 'suv', 'hatchback'

    -- 메타데이터
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    last_active_at TIMESTAMP DEFAULT NOW(),
    last_preference_update TIMESTAMP
);

-- 2. 차량 테이블
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id VARCHAR(50) PRIMARY KEY, -- 'car_001', 'car_002'
    brand VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    year INTEGER NOT NULL,
    price INTEGER NOT NULL, -- 만원 단위
    fuel_type VARCHAR(50) NOT NULL,
    transmission VARCHAR(50), -- 'manual', 'automatic', 'cvt'
    mileage INTEGER, -- 주행거리 (km)
    engine_size DECIMAL(3,1), -- 배기량 (L)
    fuel_efficiency INTEGER, -- 연비 (km/L)
    safety_rating DECIMAL(2,1), -- 안전등급 (5점 만점)
    body_type VARCHAR(50), -- 차종
    color VARCHAR(50),
    location VARCHAR(100), -- 판매 지역
    seller_type VARCHAR(50), -- 'dealer', 'individual'

    -- 이력 정보
    accident_history BOOLEAN DEFAULT false,
    owner_count INTEGER DEFAULT 1,
    maintenance_records TEXT, -- JSON 형태로 정비 기록

    -- 추천시스템용 특성 벡터 (미리 계산된 임베딩)
    feature_vector DECIMAL[], -- 512차원 특성 벡터

    -- 메타데이터
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 3. 사용자-차량 상호작용 테이블 (추천시스템 핵심)
CREATE TABLE IF NOT EXISTS user_interactions (
    interaction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    vehicle_id VARCHAR(50) REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,

    -- 상호작용 타입별 데이터
    interaction_type VARCHAR(50) NOT NULL, -- 'view', 'click', 'like', 'inquiry', 'test_drive', 'purchase'
    rating INTEGER CHECK (rating BETWEEN 1 AND 5), -- 명시적 평점
    view_duration INTEGER, -- 조회 시간 (초)
    clicked_features TEXT[], -- 클릭한 차량 특성들
    inquiry_sent BOOLEAN DEFAULT false,
    favorite_added BOOLEAN DEFAULT false,
    test_drive_requested BOOLEAN DEFAULT false,

    -- 세션 정보 (실시간 학습용)
    session_id VARCHAR(100),
    device_type VARCHAR(50), -- 'desktop', 'mobile', 'tablet'
    referrer_source VARCHAR(100), -- 유입 경로

    -- 암시적 피드백 점수 (NCF용)
    implicit_score DECIMAL(4,3) DEFAULT 1.0,

    created_at TIMESTAMP DEFAULT NOW(),

    -- 인덱스 최적화
    UNIQUE(user_id, vehicle_id, interaction_type, created_at)
);

-- 4. 추천 결과 로그 테이블
CREATE TABLE IF NOT EXISTS recommendation_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    session_id VARCHAR(100),
    algorithm_used VARCHAR(100), -- 'ncf', 'collaborative', 'content_based', 'hybrid'

    -- 추천 결과
    recommended_vehicles TEXT[], -- 추천된 차량 ID 배열
    recommendation_scores DECIMAL[], -- 각 추천 점수
    recommendation_reasons TEXT[], -- 추천 이유

    -- 성능 메트릭
    processing_time_ms INTEGER,
    model_version VARCHAR(50),
    confidence_score DECIMAL(4,3),

    -- 사용자 반응 (A/B 테스트용)
    clicked_vehicles TEXT[],
    click_through_rate DECIMAL(4,3),
    conversion_occurred BOOLEAN DEFAULT false,

    created_at TIMESTAMP DEFAULT NOW()
);

-- 5. 시장 분석 테이블 (추천 성능 향상용)
CREATE TABLE IF NOT EXISTS market_analytics (
    analytics_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id VARCHAR(50) REFERENCES vehicles(vehicle_id),
    brand VARCHAR(50),
    model VARCHAR(100),

    -- 시장 가격 정보
    avg_market_price INTEGER,
    price_trend_30d DECIMAL(5,2), -- 30일 가격 변동률 (%)

    -- 인기도 지표
    view_count_7d INTEGER DEFAULT 0,
    inquiry_count_7d INTEGER DEFAULT 0,
    favorite_count_7d INTEGER DEFAULT 0,
    popularity_score DECIMAL(4,3) DEFAULT 0,

    -- 투자 가치 지표
    depreciation_rate DECIMAL(4,3), -- 감가상각률
    resale_value_score DECIMAL(4,3), -- 리세일 가치 점수

    updated_at TIMESTAMP DEFAULT NOW()
);

-- 6. A/B 테스트 실험 테이블
CREATE TABLE IF NOT EXISTS ab_experiments (
    experiment_id VARCHAR(100) PRIMARY KEY,
    experiment_name VARCHAR(200),
    description TEXT,

    -- 실험 설정
    variants JSONB, -- {"control": "기존알고리즘", "variant_a": "NCF", "variant_b": "하이브리드"}
    traffic_split JSONB, -- {"control": 0.4, "variant_a": 0.3, "variant_b": 0.3}

    -- 실험 기간
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    is_active BOOLEAN DEFAULT true,

    created_at TIMESTAMP DEFAULT NOW()
);

-- 7. A/B 테스트 메트릭 테이블
CREATE TABLE IF NOT EXISTS ab_metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id VARCHAR(100) REFERENCES ab_experiments(experiment_id),
    user_id UUID REFERENCES users(user_id),
    variant VARCHAR(100),

    -- 메트릭 타입별 값
    metric_type VARCHAR(100), -- 'impression', 'click', 'inquiry', 'conversion'
    metric_value DECIMAL DEFAULT 1.0,

    -- 컨텍스트 정보
    session_id VARCHAR(100),
    vehicle_id VARCHAR(50),
    additional_data JSONB,

    created_at TIMESTAMP DEFAULT NOW()
);

-- 8. 모델 학습 이력 테이블
CREATE TABLE IF NOT EXISTS model_training_history (
    training_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_type VARCHAR(100), -- 'ncf', 'matrix_factorization', 'collaborative_filtering'
    model_version VARCHAR(50),

    -- 학습 데이터 정보
    training_data_size INTEGER,
    training_period_start TIMESTAMP,
    training_period_end TIMESTAMP,

    -- 하이퍼파라미터
    hyperparameters JSONB,

    -- 성능 지표
    rmse DECIMAL(6,4),
    mae DECIMAL(6,4),
    precision_at_k DECIMAL(6,4),
    recall_at_k DECIMAL(6,4),

    -- 학습 메타데이터
    training_duration_seconds INTEGER,
    training_status VARCHAR(50), -- 'completed', 'failed', 'in_progress'

    created_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_users_location ON users(location);
CREATE INDEX IF NOT EXISTS idx_users_budget ON users(budget_min, budget_max);
CREATE INDEX IF NOT EXISTS idx_users_preferences ON users USING GIN(preferred_brands);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active, last_active_at);

CREATE INDEX IF NOT EXISTS idx_vehicles_brand_model ON vehicles(brand, model);
CREATE INDEX IF NOT EXISTS idx_vehicles_price ON vehicles(price);
CREATE INDEX IF NOT EXISTS idx_vehicles_fuel_type ON vehicles(fuel_type);
CREATE INDEX IF NOT EXISTS idx_vehicles_location ON vehicles(location);
CREATE INDEX IF NOT EXISTS idx_vehicles_active ON vehicles(is_active);

CREATE INDEX IF NOT EXISTS idx_interactions_user_id ON user_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_interactions_vehicle_id ON user_interactions(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_interactions_type ON user_interactions(interaction_type);
CREATE INDEX IF NOT EXISTS idx_interactions_created_at ON user_interactions(created_at);
CREATE INDEX IF NOT EXISTS idx_interactions_session ON user_interactions(session_id);
CREATE INDEX IF NOT EXISTS idx_interactions_implicit_score ON user_interactions(implicit_score);

CREATE INDEX IF NOT EXISTS idx_recommendations_user_id ON recommendation_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_algorithm ON recommendation_logs(algorithm_used);
CREATE INDEX IF NOT EXISTS idx_recommendations_created_at ON recommendation_logs(created_at);

CREATE INDEX IF NOT EXISTS idx_market_vehicle_id ON market_analytics(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_market_updated_at ON market_analytics(updated_at);

CREATE INDEX IF NOT EXISTS idx_ab_metrics_experiment ON ab_metrics(experiment_id);
CREATE INDEX IF NOT EXISTS idx_ab_metrics_user ON ab_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_ab_metrics_variant ON ab_metrics(variant);
CREATE INDEX IF NOT EXISTS idx_ab_metrics_created_at ON ab_metrics(created_at);

-- 샘플 데이터 삽입
INSERT INTO ab_experiments (experiment_id, experiment_name, description, variants, traffic_split, start_date, end_date) VALUES
('algorithm_comparison_v1', 'NCF vs Traditional CF', '논문 기반 NCF와 전통적 협업필터링 성능 비교',
 '{"control": "collaborative_filtering", "ncf": "neural_collaborative_filtering", "hybrid": "ensemble_model"}',
 '{"control": 0.4, "ncf": 0.3, "hybrid": 0.3}',
 NOW(), NOW() + INTERVAL '30 days');

-- 뷰 생성 (자주 사용되는 쿼리 최적화)
CREATE OR REPLACE VIEW user_interaction_summary AS
SELECT
    u.user_id,
    u.name,
    u.age,
    u.location,
    u.budget_min,
    u.budget_max,
    COUNT(ui.interaction_id) as total_interactions,
    COUNT(DISTINCT ui.vehicle_id) as unique_vehicles_viewed,
    AVG(ui.view_duration) as avg_view_duration,
    COUNT(CASE WHEN ui.interaction_type = 'inquiry' THEN 1 END) as inquiry_count,
    COUNT(CASE WHEN ui.favorite_added THEN 1 END) as favorite_count,
    MAX(ui.created_at) as last_interaction
FROM users u
LEFT JOIN user_interactions ui ON u.user_id = ui.user_id
GROUP BY u.user_id, u.name, u.age, u.location, u.budget_min, u.budget_max;

CREATE OR REPLACE VIEW popular_vehicles AS
SELECT
    v.vehicle_id,
    v.brand,
    v.model,
    v.price,
    v.fuel_type,
    COUNT(ui.interaction_id) as total_views,
    COUNT(CASE WHEN ui.inquiry_sent THEN 1 END) as inquiry_count,
    AVG(ui.rating) as avg_rating,
    COUNT(CASE WHEN ui.favorite_added THEN 1 END) as favorite_count
FROM vehicles v
LEFT JOIN user_interactions ui ON v.vehicle_id = ui.vehicle_id
WHERE v.is_active = true
GROUP BY v.vehicle_id, v.brand, v.model, v.price, v.fuel_type
ORDER BY total_views DESC, avg_rating DESC;

COMMENT ON TABLE users IS '사용자 프로필 및 선호도 정보';
COMMENT ON TABLE vehicles IS '차량 기본 정보 및 특성';
COMMENT ON TABLE user_interactions IS '추천시스템 학습용 사용자-차량 상호작용 데이터';
COMMENT ON TABLE recommendation_logs IS '추천 결과 및 성능 로깅';
COMMENT ON TABLE market_analytics IS '시장 분석 및 트렌드 데이터';
COMMENT ON TABLE ab_experiments IS 'A/B 테스트 실험 설정';
COMMENT ON TABLE ab_metrics IS 'A/B 테스트 성과 메트릭';
COMMENT ON TABLE model_training_history IS '머신러닝 모델 학습 이력';