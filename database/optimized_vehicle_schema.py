"""
22컬럼 실제 차량 데이터 최적화 스키마
performance-optimized schema for rich vehicle data integration
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, ARRAY, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.indexes import Index
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import uuid
from datetime import datetime

Base = declarative_base()

class VehicleCondition(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"

class SellType(Enum):
    DEALER = "dealer"
    INDIVIDUAL = "individual"
    AUCTION = "auction"

@dataclass
class VehicleFeatureVector:
    """NCF 모델용 최적화된 차량 특성 벡터"""
    # 카테고리형 특성 (임베딩용)
    manufacturer_id: int
    model_id: int
    cartype_id: int
    fueltype_id: int
    transmission_id: int
    color_id: int
    location_id: int

    # 수치형 특성 (정규화된)
    price_normalized: float
    year_normalized: float
    distance_normalized: float

    # 파생 특성
    price_per_year: float
    depreciation_rate: float
    market_position_score: float

class OptimizedVehicleData(Base):
    """22컬럼 실제 차량 데이터 최적화 테이블"""
    __tablename__ = 'optimized_vehicles'

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 원본 식별자 (ARRAY 타입 지원)
    vehicleid = Column(ARRAY(String), nullable=True, index=True)
    carseq = Column(ARRAY(Integer), nullable=True, index=True)
    vehicleno = Column(String(50), nullable=True, index=True)

    # 기본 속성 (인덱싱 최적화)
    manufacturer = Column(String(50), nullable=False, index=True)
    model = Column(String(100), nullable=False, index=True)
    generation = Column(String(50), nullable=True)
    trim = Column(String(100), nullable=True)

    # 성능 정보 (필터링 최적화)
    fueltype = Column(String(30), nullable=False, index=True)
    transmission = Column(String(20), nullable=False, index=True)
    cartype = Column(String(30), nullable=False, index=True)

    # 외관
    colorname = Column(String(30), nullable=True, index=True)

    # 시간/거리 정보 (ARRAY 타입, 범위 쿼리 최적화)
    modelyear = Column(ARRAY(Integer), nullable=True, index=True)
    firstregistrationdate = Column(ARRAY(DateTime), nullable=True, index=True)
    distance = Column(ARRAY(Float), nullable=True, index=True)

    # 가격 정보 (범위 쿼리 최적화)
    price = Column(ARRAY(Float), nullable=False, index=True)
    originprice = Column(ARRAY(Float), nullable=True, index=True)

    # 판매 정보
    selltype = Column(String(20), nullable=True, index=True)
    location = Column(String(100), nullable=True, index=True)
    platform = Column(String(50), nullable=True)
    origin = Column(String(50), nullable=True)

    # 미디어
    detailurl = Column(Text, nullable=True)
    photo = Column(Text, nullable=True)

    # 추천 시스템 최적화 필드
    feature_vector = Column(JSON, nullable=True)  # 미리 계산된 특성 벡터
    embedding_version = Column(Integer, default=1)  # 임베딩 버전 관리

    # 성능 최적화 필드
    price_min = Column(Float, nullable=True, index=True)  # 가격 범위 쿼리용
    price_max = Column(Float, nullable=True, index=True)
    year_min = Column(Integer, nullable=True, index=True)  # 연식 범위 쿼리용
    year_max = Column(Integer, nullable=True, index=True)
    distance_min = Column(Float, nullable=True, index=True)  # 주행거리 범위 쿼리용
    distance_max = Column(Float, nullable=True, index=True)

    # 메타데이터
    data_quality_score = Column(Float, default=1.0)  # 데이터 품질 점수
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_interaction_at = Column(DateTime, nullable=True, index=True)  # 마지막 상호작용 시간

    # 복합 인덱스 (성능 최적화)
    __table_args__ = (
        # 주요 검색 패턴 최적화
        Index('idx_manufacturer_model_year', 'manufacturer', 'model', 'year_min'),
        Index('idx_cartype_fueltype_price', 'cartype', 'fueltype', 'price_min'),
        Index('idx_location_selltype_active', 'location', 'selltype', 'is_active'),
        Index('idx_price_range', 'price_min', 'price_max'),
        Index('idx_year_range', 'year_min', 'year_max'),
        Index('idx_active_created', 'is_active', 'created_at'),

        # 추천 시스템 최적화
        Index('idx_feature_embedding', 'embedding_version', 'data_quality_score'),
        Index('idx_interaction_recency', 'last_interaction_at', 'is_active'),

        # 분석 쿼리 최적화
        Index('idx_manufacturer_cartype_location', 'manufacturer', 'cartype', 'location'),
        Index('idx_fueltype_transmission_year', 'fueltype', 'transmission', 'year_min'),
    )

class VehicleAnalytics(Base):
    """차량별 분석 및 통계 정보"""
    __tablename__ = 'vehicle_analytics'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # 추천 시스템 메트릭
    view_count_7d = Column(Integer, default=0)
    view_count_30d = Column(Integer, default=0)
    inquiry_count_7d = Column(Integer, default=0)
    inquiry_count_30d = Column(Integer, default=0)
    favorite_count = Column(Integer, default=0)

    # 시장 분석
    market_position_percentile = Column(Float, nullable=True)  # 가격 대비 시장 위치
    popularity_score = Column(Float, default=0.0, index=True)
    competition_score = Column(Float, nullable=True)  # 유사 차량 경쟁도

    # 가격 분석
    price_competitiveness = Column(Float, nullable=True)  # 가격 경쟁력
    price_change_rate_30d = Column(Float, nullable=True)  # 30일 가격 변동률
    estimated_depreciation = Column(Float, nullable=True)  # 추정 감가상각률

    # 사용자 행동 패턴
    avg_view_duration = Column(Float, nullable=True)  # 평균 조회 시간
    bounce_rate = Column(Float, nullable=True)  # 이탈률
    conversion_rate = Column(Float, nullable=True)  # 전환율

    # 메타데이터
    calculated_at = Column(DateTime, default=datetime.utcnow, index=True)
    is_current = Column(Boolean, default=True, index=True)

    __table_args__ = (
        Index('idx_vehicle_analytics_current', 'vehicle_id', 'is_current'),
        Index('idx_popularity_position', 'popularity_score', 'market_position_percentile'),
        Index('idx_calculated_current', 'calculated_at', 'is_current'),
    )

class VehicleSearchIndex(Base):
    """검색 최적화 전용 테이블"""
    __tablename__ = 'vehicle_search_index'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # 텍스트 검색 최적화
    search_text = Column(Text, nullable=False)  # 전체 텍스트 검색용
    search_keywords = Column(ARRAY(String), nullable=True, index=True)  # 키워드 배열

    # 카테고리 ID (빠른 필터링용)
    manufacturer_id = Column(Integer, nullable=False, index=True)
    model_id = Column(Integer, nullable=False, index=True)
    cartype_id = Column(Integer, nullable=False, index=True)
    fueltype_id = Column(Integer, nullable=False, index=True)
    transmission_id = Column(Integer, nullable=False, index=True)
    color_id = Column(Integer, nullable=True, index=True)
    location_id = Column(Integer, nullable=True, index=True)

    # 범위 검색 최적화
    price_bucket = Column(Integer, nullable=True, index=True)  # 가격 구간 (백만원 단위)
    year_bucket = Column(Integer, nullable=True, index=True)   # 연식 구간 (5년 단위)
    distance_bucket = Column(Integer, nullable=True, index=True)  # 주행거리 구간

    # 추천 시스템 특성
    feature_hash = Column(String(64), nullable=True, index=True)  # 특성 해시 (유사 차량 검색)
    similarity_cluster = Column(Integer, nullable=True, index=True)  # 유사성 클러스터

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        # 멀티 필터 검색 최적화
        Index('idx_search_multi_filter', 'manufacturer_id', 'cartype_id', 'price_bucket'),
        Index('idx_search_fuel_transmission', 'fueltype_id', 'transmission_id', 'year_bucket'),
        Index('idx_search_location_price', 'location_id', 'price_bucket', 'distance_bucket'),

        # 유사성 검색 최적화
        Index('idx_similarity_cluster', 'similarity_cluster', 'feature_hash'),

        # 텍스트 검색 최적화 (PostgreSQL GIN 인덱스)
        Index('idx_search_keywords', 'search_keywords', postgresql_using='gin'),
    )

# 룩업 테이블들 (정규화 및 성능 최적화)
class ManufacturerLookup(Base):
    __tablename__ = 'manufacturer_lookup'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    name_normalized = Column(String(50), nullable=False, index=True)  # 검색 최적화
    popularity_rank = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ModelLookup(Base):
    __tablename__ = 'model_lookup'
    id = Column(Integer, primary_key=True)
    manufacturer_id = Column(Integer, nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    name_normalized = Column(String(100), nullable=False, index=True)
    popularity_rank = Column(Integer, nullable=True)
    avg_price_range = Column(String(20), nullable=True)  # 가격대 정보
    created_at = Column(DateTime, default=datetime.utcnow)

class CarTypeLookup(Base):
    __tablename__ = 'cartype_lookup'
    id = Column(Integer, primary_key=True)
    name = Column(String(30), unique=True, nullable=False, index=True)
    category = Column(String(20), nullable=True)  # sedan, suv, hatchback 등
    size_category = Column(String(20), nullable=True)  # compact, mid, full
    popularity_rank = Column(Integer, nullable=True)

class FuelTypeLookup(Base):
    __tablename__ = 'fueltype_lookup'
    id = Column(Integer, primary_key=True)
    name = Column(String(30), unique=True, nullable=False, index=True)
    category = Column(String(20), nullable=True)  # gasoline, hybrid, electric
    efficiency_score = Column(Float, nullable=True)  # 연비 점수
    eco_friendly_rank = Column(Integer, nullable=True)

class LocationLookup(Base):
    __tablename__ = 'location_lookup'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    region = Column(String(50), nullable=True, index=True)  # 서울, 경기, 부산 등
    market_size = Column(String(20), nullable=True)  # large, medium, small
    avg_price_premium = Column(Float, default=1.0)  # 지역별 가격 프리미엄

# 데이터 품질 및 검증 규칙
VEHICLE_DATA_QUALITY_RULES = {
    "required_fields": [
        "manufacturer", "model", "cartype", "fueltype",
        "transmission", "price"
    ],
    "price_validation": {
        "min_price": 1000000,  # 100만원
        "max_price": 500000000,  # 5억원
        "price_ratio_threshold": 10.0  # 원가 대비 현재가 비율
    },
    "year_validation": {
        "min_year": 1990,
        "max_year": datetime.now().year + 1
    },
    "distance_validation": {
        "max_distance": 500000,  # 50만km
        "distance_per_year_threshold": 30000  # 연간 3만km 이상시 검토
    }
}