"""
22개 컬럼 vehicles 테이블 ARRAY 데이터 최적화 전략
PostgreSQL ARRAY 타입 효율적 처리 및 성능 최적화
"""
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime
import pandas as pd

class ArrayColumnType(Enum):
    """ARRAY 컬럼 타입 분류"""
    IDENTIFIER = "identifier"  # vehicleid, carseq
    TEMPORAL = "temporal"      # modelyear, firstregistrationdate
    NUMERIC = "numeric"        # distance, price, originprice

@dataclass
class ArrayOptimizationStrategy:
    """각 ARRAY 컬럼별 최적화 전략"""
    column_name: str
    column_type: ArrayColumnType
    indexing_strategy: str
    query_optimization: str
    api_serialization: str
    frontend_rendering: str

# 7개 ARRAY 컬럼별 최적화 전략 정의
ARRAY_OPTIMIZATION_STRATEGIES = {
    'vehicleid': ArrayOptimizationStrategy(
        column_name='vehicleid',
        column_type=ArrayColumnType.IDENTIFIER,
        indexing_strategy='GIN index for fast containment searches',
        query_optimization='Use ANY() for efficient searches',
        api_serialization='Return first value as primary ID',
        frontend_rendering='Display primary ID with count indicator'
    ),

    'carseq': ArrayOptimizationStrategy(
        column_name='carseq',
        column_type=ArrayColumnType.IDENTIFIER,
        indexing_strategy='GIN index for sequence searches',
        query_optimization='Range queries with array slicing',
        api_serialization='Return as sorted array',
        frontend_rendering='Show sequence range (min-max)'
    ),

    'modelyear': ArrayOptimizationStrategy(
        column_name='modelyear',
        column_type=ArrayColumnType.TEMPORAL,
        indexing_strategy='GIN index + computed min/max columns',
        query_optimization='Range filters using extracted bounds',
        api_serialization='Include year_range summary',
        frontend_rendering='Display year range with picker'
    ),

    'firstregistrationdate': ArrayOptimizationStrategy(
        column_name='firstregistrationdate',
        column_type=ArrayColumnType.TEMPORAL,
        indexing_strategy='GIN index + computed date range columns',
        query_optimization='Date range queries with bounds',
        api_serialization='Format dates consistently',
        frontend_rendering='Show registration timeline'
    ),

    'distance': ArrayOptimizationStrategy(
        column_name='distance',
        column_type=ArrayColumnType.NUMERIC,
        indexing_strategy='GIN index + min/max computed columns',
        query_optimization='Range queries with computed bounds',
        api_serialization='Include mileage summary stats',
        frontend_rendering='Display mileage range with histogram'
    ),

    'price': ArrayOptimizationStrategy(
        column_name='price',
        column_type=ArrayColumnType.NUMERIC,
        indexing_strategy='GIN index + price statistics columns',
        query_optimization='Price range filters with pre-computed stats',
        api_serialization='Include price analysis (min/max/avg)',
        frontend_rendering='Price range with market position'
    ),

    'originprice': ArrayOptimizationStrategy(
        column_name='originprice',
        column_type=ArrayColumnType.NUMERIC,
        indexing_strategy='GIN index + discount calculation columns',
        query_optimization='Discount analysis with computed fields',
        api_serialization='Include discount percentage',
        frontend_rendering='Show price history with savings'
    )
}

class VehicleArrayProcessor:
    """ARRAY 컬럼 효율적 처리를 위한 프로세서"""

    def __init__(self):
        self.strategies = ARRAY_OPTIMIZATION_STRATEGIES

    def generate_computed_columns_sql(self) -> str:
        """성능 최적화를 위한 computed column 생성 SQL"""
        sql_statements = []

        # 수치형 ARRAY 컬럼들의 min/max 계산 컬럼
        numeric_arrays = ['distance', 'price', 'originprice']
        for col in numeric_arrays:
            sql_statements.extend([
                f"ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS {col}_min DECIMAL",
                f"ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS {col}_max DECIMAL",
                f"ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS {col}_avg DECIMAL"
            ])

        # 시간 관련 ARRAY 컬럼들의 범위 계산 컬럼
        temporal_arrays = [
            ('modelyear', 'INTEGER'),
            ('firstregistrationdate', 'DATE')
        ]
        for col, datatype in temporal_arrays:
            sql_statements.extend([
                f"ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS {col}_min {datatype}",
                f"ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS {col}_max {datatype}"
            ])

        # 파생 컬럼들
        derived_columns = [
            "ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS discount_percentage DECIMAL",
            "ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS price_per_year DECIMAL",
            "ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS depreciation_rate DECIMAL"
        ]
        sql_statements.extend(derived_columns)

        return ";\n".join(sql_statements) + ";"

    def generate_indexes_sql(self) -> str:
        """성능 최적화 인덱스 생성 SQL"""
        index_statements = [
            # GIN 인덱스 (ARRAY 검색 최적화)
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vehicles_vehicleid_gin ON vehicles USING GIN (vehicleid)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vehicles_carseq_gin ON vehicles USING GIN (carseq)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vehicles_modelyear_gin ON vehicles USING GIN (modelyear)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vehicles_distance_gin ON vehicles USING GIN (distance)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vehicles_price_gin ON vehicles USING GIN (price)",

            # 범위 검색 최적화 (computed columns)
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vehicles_price_range ON vehicles (price_min, price_max)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vehicles_year_range ON vehicles (modelyear_min, modelyear_max)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vehicles_distance_range ON vehicles (distance_min, distance_max)",

            # 복합 인덱스 (일반적인 검색 패턴)
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vehicles_search_primary ON vehicles (manufacturer, cartype, price_min, modelyear_min)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vehicles_search_location ON vehicles (location, fueltype, price_min)",

            # 텍스트 검색 최적화
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vehicles_text_search ON vehicles USING GIN (to_tsvector('english', manufacturer || ' ' || model || ' ' || trim))"
        ]

        return ";\n".join(index_statements) + ";"

    def generate_update_triggers_sql(self) -> str:
        """computed column 자동 업데이트 트리거 생성 SQL"""

        trigger_function = """
        CREATE OR REPLACE FUNCTION update_vehicle_computed_columns()
        RETURNS TRIGGER AS $$
        BEGIN
            -- 가격 관련 계산
            IF NEW.price IS NOT NULL AND array_length(NEW.price, 1) > 0 THEN
                NEW.price_min := (SELECT MIN(unnest) FROM unnest(NEW.price));
                NEW.price_max := (SELECT MAX(unnest) FROM unnest(NEW.price));
                NEW.price_avg := (SELECT AVG(unnest) FROM unnest(NEW.price));
            END IF;

            -- 주행거리 관련 계산
            IF NEW.distance IS NOT NULL AND array_length(NEW.distance, 1) > 0 THEN
                NEW.distance_min := (SELECT MIN(unnest) FROM unnest(NEW.distance));
                NEW.distance_max := (SELECT MAX(unnest) FROM unnest(NEW.distance));
                NEW.distance_avg := (SELECT AVG(unnest) FROM unnest(NEW.distance));
            END IF;

            -- 원가 관련 계산
            IF NEW.originprice IS NOT NULL AND array_length(NEW.originprice, 1) > 0 THEN
                NEW.originprice_min := (SELECT MIN(unnest) FROM unnest(NEW.originprice));
                NEW.originprice_max := (SELECT MAX(unnest) FROM unnest(NEW.originprice));
                NEW.originprice_avg := (SELECT AVG(unnest) FROM unnest(NEW.originprice));
            END IF;

            -- 연식 관련 계산
            IF NEW.modelyear IS NOT NULL AND array_length(NEW.modelyear, 1) > 0 THEN
                NEW.modelyear_min := (SELECT MIN(unnest) FROM unnest(NEW.modelyear));
                NEW.modelyear_max := (SELECT MAX(unnest) FROM unnest(NEW.modelyear));
            END IF;

            -- 등록일 관련 계산
            IF NEW.firstregistrationdate IS NOT NULL AND array_length(NEW.firstregistrationdate, 1) > 0 THEN
                NEW.firstregistrationdate_min := (SELECT MIN(unnest) FROM unnest(NEW.firstregistrationdate));
                NEW.firstregistrationdate_max := (SELECT MAX(unnest) FROM unnest(NEW.firstregistrationdate));
            END IF;

            -- 할인율 계산
            IF NEW.price_avg IS NOT NULL AND NEW.originprice_avg IS NOT NULL AND NEW.originprice_avg > 0 THEN
                NEW.discount_percentage := ((NEW.originprice_avg - NEW.price_avg) / NEW.originprice_avg) * 100;
            END IF;

            -- 연간 가격 계산 (평균 가격 / 연식)
            IF NEW.price_avg IS NOT NULL AND NEW.modelyear_max IS NOT NULL AND NEW.modelyear_max > 0 THEN
                NEW.price_per_year := NEW.price_avg / (2024 - NEW.modelyear_max + 1);
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """

        trigger_creation = """
        DROP TRIGGER IF EXISTS trigger_update_vehicle_computed ON vehicles;
        CREATE TRIGGER trigger_update_vehicle_computed
            BEFORE INSERT OR UPDATE ON vehicles
            FOR EACH ROW
            EXECUTE FUNCTION update_vehicle_computed_columns();
        """

        return trigger_function + "\n\n" + trigger_creation

    def optimize_query_for_array_search(self, filters: Dict[str, Any]) -> str:
        """ARRAY 검색 최적화된 쿼리 생성"""
        conditions = []

        # 가격 범위 검색 (computed columns 활용)
        if 'price_min' in filters and 'price_max' in filters:
            conditions.append(f"price_min <= {filters['price_max']} AND price_max >= {filters['price_min']}")

        # 연식 범위 검색
        if 'year_min' in filters and 'year_max' in filters:
            conditions.append(f"modelyear_min <= {filters['year_max']} AND modelyear_max >= {filters['year_min']}")

        # 주행거리 범위 검색
        if 'distance_max' in filters:
            conditions.append(f"distance_min <= {filters['distance_max']}")

        # ARRAY 포함 검색 (GIN 인덱스 활용)
        if 'vehicle_ids' in filters:
            vehicle_ids_str = "'{" + ','.join(map(str, filters['vehicle_ids'])) + "}'"
            conditions.append(f"vehicleid && {vehicle_ids_str}")

        # 일반 텍스트 필터
        text_filters = ['manufacturer', 'cartype', 'fueltype', 'location']
        for field in text_filters:
            if field in filters and filters[field]:
                conditions.append(f"{field} = '{filters[field]}'")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        return f"""
        SELECT
            vehicleid[1] as primary_vehicleid,
            vehicleno, manufacturer, model, cartype, fueltype,
            price_min, price_max, price_avg,
            distance_min, distance_max,
            modelyear_min, modelyear_max,
            discount_percentage, price_per_year,
            location, selltype, photo
        FROM vehicles
        WHERE {where_clause}
        ORDER BY price_avg ASC
        """

class VehicleApiOptimizer:
    """API 응답 최적화를 위한 데이터 직렬화"""

    def optimize_vehicle_response(self, vehicle_data: Dict[str, Any]) -> Dict[str, Any]:
        """22개 컬럼 데이터를 효율적으로 직렬화"""

        optimized = {
            # 기본 식별 정보
            "id": vehicle_data.get('vehicleid', [None])[0] if vehicle_data.get('vehicleid') else None,
            "vehicleno": vehicle_data.get('vehicleno'),

            # 차량 기본 정보
            "vehicle_info": {
                "manufacturer": vehicle_data.get('manufacturer'),
                "model": vehicle_data.get('model'),
                "generation": vehicle_data.get('generation'),
                "trim": vehicle_data.get('trim'),
                "cartype": vehicle_data.get('cartype'),
                "fueltype": vehicle_data.get('fueltype'),
                "transmission": vehicle_data.get('transmission'),
                "colorname": vehicle_data.get('colorname')
            },

            # 가격 정보 (ARRAY → 요약)
            "pricing": self._optimize_price_data(vehicle_data),

            # 연식/등록 정보 (ARRAY → 요약)
            "temporal_info": self._optimize_temporal_data(vehicle_data),

            # 주행거리 정보 (ARRAY → 요약)
            "mileage_info": self._optimize_mileage_data(vehicle_data),

            # 판매 정보
            "sale_info": {
                "selltype": vehicle_data.get('selltype'),
                "location": vehicle_data.get('location'),
                "platform": vehicle_data.get('platform'),
                "origin": vehicle_data.get('origin')
            },

            # 미디어
            "media": {
                "detailurl": vehicle_data.get('detailurl'),
                "photo": vehicle_data.get('photo')
            }
        }

        return optimized

    def _optimize_price_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """가격 ARRAY 데이터 최적화"""
        price_array = data.get('price', [])
        origin_array = data.get('originprice', [])

        if not price_array:
            return {"current": None, "original": None, "discount": 0}

        current_prices = [p for p in price_array if p is not None]
        original_prices = [p for p in origin_array if p is not None] if origin_array else []

        current_price = min(current_prices) if current_prices else None
        original_price = min(original_prices) if original_prices else current_price

        discount = 0
        if current_price and original_price and original_price > current_price:
            discount = round(((original_price - current_price) / original_price) * 100, 1)

        return {
            "current": current_price,
            "original": original_price,
            "discount_percentage": discount,
            "price_range": {
                "min": min(current_prices) if current_prices else None,
                "max": max(current_prices) if current_prices else None
            }
        }

    def _optimize_temporal_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """시간 관련 ARRAY 데이터 최적화"""
        year_array = data.get('modelyear', [])
        reg_array = data.get('firstregistrationdate', [])

        years = [y for y in year_array if y is not None] if year_array else []

        return {
            "model_year": {
                "primary": max(years) if years else None,
                "range": {"min": min(years), "max": max(years)} if years else None
            },
            "registration": {
                "first_date": min(reg_array) if reg_array else None,
                "latest_date": max(reg_array) if reg_array else None
            }
        }

    def _optimize_mileage_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """주행거리 ARRAY 데이터 최적화"""
        distance_array = data.get('distance', [])
        distances = [d for d in distance_array if d is not None] if distance_array else []

        if not distances:
            return {"current": None, "range": None}

        return {
            "current": min(distances),  # 최신(최소) 주행거리
            "range": {
                "min": min(distances),
                "max": max(distances)
            },
            "average": round(sum(distances) / len(distances), 1) if distances else None
        }

# 사용 예시 및 테스트 함수들
def setup_vehicle_table_optimization():
    """vehicles 테이블 최적화 설정 실행"""
    processor = VehicleArrayProcessor()

    print("=== Vehicle Table Optimization Setup ===")
    print("\n1. Computed Columns SQL:")
    print(processor.generate_computed_columns_sql())

    print("\n2. Indexes SQL:")
    print(processor.generate_indexes_sql())

    print("\n3. Triggers SQL:")
    print(processor.generate_update_triggers_sql())

if __name__ == "__main__":
    setup_vehicle_table_optimization()