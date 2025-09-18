"""
차량 전문 에이전트를 위한 통합 데이터 레이어
모든 차량 관련 테이블에 자유롭게 접근 가능한 확장 가능한 아키텍처
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
import pandas as pd
import json
from dataclasses import dataclass
from enum import Enum
from config.database import DatabaseManager

logger = logging.getLogger(__name__)

class TableCategory(Enum):
    """테이블 카테고리 분류"""
    CORE_VEHICLE = "core_vehicle"           # 핵심 차량 데이터
    USER_DATA = "user_data"                 # 사용자 관련 데이터
    INTERACTION = "interaction"             # 상호작용 데이터
    FINANCIAL = "financial"                 # 금융 관련 데이터
    MARKET = "market"                       # 시장 분석 데이터
    MAINTENANCE = "maintenance"             # 정비/이력 데이터
    INSURANCE = "insurance"                 # 보험 관련 데이터
    REVIEWS = "reviews"                     # 리뷰/평가 데이터
    ANALYTICS = "analytics"                 # 분석/로그 데이터

@dataclass
class TableInfo:
    """테이블 정보 정의"""
    name: str
    category: TableCategory
    description: str
    key_columns: List[str]
    relationships: Dict[str, str]  # {related_table: join_column}
    data_types: Dict[str, str]
    is_array_table: bool = False   # ARRAY 컬럼 포함 여부
    array_columns: List[str] = None

class UniversalVehicleDataLayer:
    """
    차량 전문 에이전트를 위한 통합 데이터 접근 레이어
    모든 차량 관련 테이블을 자유롭게 조회/분석 가능
    """

    def __init__(self):
        self.db = DatabaseManager()
        self.table_registry = self._initialize_table_registry()
        self.query_cache = {}
        self.cache_ttl = 300  # 5분 캐시

    def _initialize_table_registry(self) -> Dict[str, TableInfo]:
        """테이블 레지스트리 초기화 - 확장 가능한 구조"""

        registry = {
            # 핵심 차량 데이터
            "vehicles": TableInfo(
                name="vehicles",
                category=TableCategory.CORE_VEHICLE,
                description="22개 컬럼 메인 차량 데이터 (ARRAY 포함)",
                key_columns=["vehicleid", "vehicleno", "manufacturer", "model"],
                relationships={
                    "user_interactions": "vehicleid",
                    "recommendations": "vehicle_id",
                    "matches": "vehicle_id"
                },
                data_types={
                    "vehicleid": "ARRAY",
                    "carseq": "ARRAY",
                    "price": "ARRAY",
                    "distance": "ARRAY",
                    "modelyear": "ARRAY",
                    "manufacturer": "VARCHAR",
                    "model": "VARCHAR"
                },
                is_array_table=True,
                array_columns=["vehicleid", "carseq", "modelyear", "firstregistrationdate",
                              "distance", "price", "originprice"]
            ),

            # 사용자 데이터
            "users": TableInfo(
                name="users",
                category=TableCategory.USER_DATA,
                description="사용자 프로필 및 선호도 정보",
                key_columns=["user_id", "email", "preferences"],
                relationships={
                    "user_interactions": "user_id",
                    "recommendations": "user_id"
                },
                data_types={"user_id": "VARCHAR", "preferences": "JSON"}
            ),

            # 상호작용 데이터
            "user_interactions": TableInfo(
                name="user_interactions",
                category=TableCategory.INTERACTION,
                description="사용자-차량 상호작용 로그",
                key_columns=["user_id", "vehicle_id", "interaction_type", "created_at"],
                relationships={
                    "users": "user_id",
                    "vehicles": "vehicle_id"
                },
                data_types={"interaction_type": "VARCHAR", "created_at": "TIMESTAMP"}
            ),

            # 금융 관련 데이터
            "financial_products": TableInfo(
                name="financial_products",
                category=TableCategory.FINANCIAL,
                description="금융 상품 정보",
                key_columns=["product_id", "product_type", "interest_rate"],
                relationships={"loan_rates": "product_id"},
                data_types={"product_type": "VARCHAR", "interest_rate": "DECIMAL"}
            ),

            "loan_product": TableInfo(
                name="loan_product",
                category=TableCategory.FINANCIAL,
                description="대출 상품 상세 정보",
                key_columns=["loan_id", "vehicle_price_range", "loan_term"],
                relationships={"financial_products": "product_id"},
                data_types={"loan_term": "INTEGER", "vehicle_price_range": "VARCHAR"}
            ),

            "loan_rates": TableInfo(
                name="loan_rates",
                category=TableCategory.FINANCIAL,
                description="대출 금리 정보",
                key_columns=["rate_id", "credit_score", "interest_rate"],
                relationships={"loan_product": "loan_id"},
                data_types={"credit_score": "VARCHAR", "interest_rate": "DECIMAL"}
            ),

            # 추천/매칭 데이터
            "recommendations": TableInfo(
                name="recommendations",
                category=TableCategory.ANALYTICS,
                description="추천 결과 로그",
                key_columns=["recommendation_id", "user_id", "vehicle_id", "score"],
                relationships={
                    "users": "user_id",
                    "vehicles": "vehicle_id"
                },
                data_types={"score": "DECIMAL", "algorithm": "VARCHAR"}
            ),

            "matches": TableInfo(
                name="matches",
                category=TableCategory.ANALYTICS,
                description="사용자-차량 매칭 데이터",
                key_columns=["match_id", "user_id", "vehicle_id", "match_score"],
                relationships={
                    "users": "user_id",
                    "vehicles": "vehicle_id"
                },
                data_types={"match_score": "DECIMAL"}
            )
        }

        # 미래 확장을 위한 예상 테이블들 (아직 존재하지 않음)
        future_tables = self._define_future_tables()
        registry.update(future_tables)

        return registry

    def _define_future_tables(self) -> Dict[str, TableInfo]:
        """미래 확장될 테이블들 사전 정의"""
        return {
            # 시장 분석 데이터 (미래)
            "market_analytics": TableInfo(
                name="market_analytics",
                category=TableCategory.MARKET,
                description="시장 분석 및 가격 트렌드 데이터",
                key_columns=["vehicle_id", "market_price", "trend_score"],
                relationships={"vehicles": "vehicle_id"},
                data_types={"market_price": "DECIMAL", "trend_score": "DECIMAL"}
            ),

            # 차량 리뷰 데이터 (미래)
            "vehicle_reviews": TableInfo(
                name="vehicle_reviews",
                category=TableCategory.REVIEWS,
                description="사용자 차량 리뷰 및 평가",
                key_columns=["review_id", "vehicle_id", "user_id", "rating"],
                relationships={
                    "vehicles": "vehicle_id",
                    "users": "user_id"
                },
                data_types={"rating": "DECIMAL", "review_text": "TEXT"}
            ),

            # 정비 이력 데이터 (미래)
            "maintenance_records": TableInfo(
                name="maintenance_records",
                category=TableCategory.MAINTENANCE,
                description="차량 정비 및 수리 이력",
                key_columns=["maintenance_id", "vehicle_id", "service_date", "service_type"],
                relationships={"vehicles": "vehicle_id"},
                data_types={"service_date": "DATE", "cost": "DECIMAL"}
            ),

            # 보험 데이터 (미래)
            "insurance_data": TableInfo(
                name="insurance_data",
                category=TableCategory.INSURANCE,
                description="차량 보험 정보 및 보험료 데이터",
                key_columns=["insurance_id", "vehicle_id", "premium", "coverage_type"],
                relationships={"vehicles": "vehicle_id"},
                data_types={"premium": "DECIMAL", "coverage_type": "VARCHAR"}
            )
        }

    # =========================
    # 핵심 데이터 접근 메서드들
    # =========================

    async def get_comprehensive_vehicle_data(
        self,
        vehicle_id: str = None,
        filters: Dict[str, Any] = None,
        include_related: bool = True,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        차량 전문 에이전트를 위한 종합 차량 데이터 조회
        모든 관련 테이블 데이터를 한 번에 가져옴
        """
        try:
            result = {
                "vehicles": [],
                "related_data": {},
                "market_context": {},
                "user_interactions": {},
                "financial_options": {},
                "metadata": {}
            }

            # 1. 메인 차량 데이터 조회 (22개 컬럼 ARRAY 포함)
            vehicle_data = await self._query_vehicle_table(vehicle_id, filters, limit)
            result["vehicles"] = vehicle_data

            if not vehicle_data:
                return result

            vehicle_ids = [v.get("vehicle_id") or v.get("vehicleid") for v in vehicle_data]

            if include_related:
                # 2. 관련 테이블 데이터 병렬 조회
                related_tasks = [
                    self._get_user_interaction_data(vehicle_ids),
                    self._get_financial_data_for_vehicles(vehicle_ids),
                    self._get_recommendation_history(vehicle_ids),
                    self._get_market_analysis_data(vehicle_ids)
                ]

                related_results = await asyncio.gather(*related_tasks, return_exceptions=True)

                result["user_interactions"] = related_results[0] if len(related_results) > 0 else {}
                result["financial_options"] = related_results[1] if len(related_results) > 1 else {}
                result["recommendation_history"] = related_results[2] if len(related_results) > 2 else {}
                result["market_context"] = related_results[3] if len(related_results) > 3 else {}

            # 3. 메타데이터 생성
            result["metadata"] = {
                "query_timestamp": datetime.now().isoformat(),
                "total_vehicles": len(vehicle_data),
                "data_sources": list(self.table_registry.keys()),
                "array_columns_processed": True,
                "comprehensive_analysis": include_related
            }

            return result

        except Exception as e:
            logger.error(f"❌ 종합 차량 데이터 조회 실패: {e}")
            return {"error": str(e), "vehicles": []}

    async def _query_vehicle_table(
        self,
        vehicle_id: str = None,
        filters: Dict[str, Any] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """vehicles 테이블 쿼리 (22개 컬럼 ARRAY 처리 포함)"""

        # 기본 쿼리 - 모든 22개 컬럼 조회
        base_query = """
        SELECT
            vehicleid, carseq, vehicleno, platform, origin,
            cartype, manufacturer, model, generation, trim,
            fueltype, transmission, colorname,
            modelyear, firstregistrationdate, distance,
            price, originprice, selltype, location,
            detailurl, photo
        FROM vehicles
        WHERE 1=1
        """

        conditions = []
        params = []

        # 특정 차량 ID 조회
        if vehicle_id:
            conditions.append("(vehicleno = %s OR %s = ANY(vehicleid))")
            params.extend([vehicle_id, vehicle_id])

        # 필터 조건 추가
        if filters:
            filter_conditions, filter_params = self._build_filter_conditions(filters)
            if filter_conditions:
                conditions.extend(filter_conditions)
                params.extend(filter_params)

        # 조건 적용
        if conditions:
            base_query += " AND " + " AND ".join(conditions)

        base_query += f" ORDER BY vehicleno LIMIT {limit}"

        try:
            df = pd.read_sql(base_query, self.db.engine, params=params if params else None)

            # ARRAY 데이터 처리된 결과 반환
            return [self._process_vehicle_row(row.to_dict()) for _, row in df.iterrows()]

        except Exception as e:
            logger.error(f"❌ vehicles 테이블 쿼리 실패: {e}")
            return []

    def _process_vehicle_row(self, row_data: Dict[str, Any]) -> Dict[str, Any]:
        """차량 행 데이터 처리 (ARRAY 컬럼 가공 포함)"""

        processed = row_data.copy()

        # ARRAY 컬럼들 처리
        array_columns = ["vehicleid", "carseq", "modelyear", "firstregistrationdate",
                        "distance", "price", "originprice"]

        for col in array_columns:
            if col in processed and processed[col] is not None:
                processed[f"{col}_processed"] = self._process_array_column(processed[col])

        # 분석용 필드 추가
        processed["analysis"] = {
            "price_analysis": self._analyze_price_array(row_data.get("price"), row_data.get("originprice")),
            "year_analysis": self._analyze_year_array(row_data.get("modelyear")),
            "mileage_analysis": self._analyze_distance_array(row_data.get("distance")),
            "has_multiple_prices": bool(self._get_array_length(row_data.get("price")) > 1),
            "data_richness_score": self._calculate_data_richness(row_data)
        }

        return processed

    def _process_array_column(self, array_data: Any) -> Dict[str, Any]:
        """ARRAY 컬럼 데이터 처리"""
        if array_data is None:
            return {"values": [], "count": 0, "summary": None}

        # PostgreSQL ARRAY를 Python 리스트로 변환
        values = self._array_to_list(array_data)

        if not values:
            return {"values": [], "count": 0, "summary": None}

        # 수치형 데이터인 경우 통계 계산
        numeric_values = []
        for v in values:
            try:
                if v is not None:
                    numeric_values.append(float(v))
            except (ValueError, TypeError):
                pass

        summary = {}
        if numeric_values:
            summary = {
                "min": min(numeric_values),
                "max": max(numeric_values),
                "avg": sum(numeric_values) / len(numeric_values),
                "count": len(numeric_values)
            }

        return {
            "values": values,
            "count": len(values),
            "summary": summary,
            "is_numeric": bool(numeric_values)
        }

    def _array_to_list(self, array_data: Any) -> List[Any]:
        """PostgreSQL ARRAY를 Python 리스트로 변환"""
        if array_data is None:
            return []

        if isinstance(array_data, list):
            return array_data

        if isinstance(array_data, str) and array_data.startswith('{') and array_data.endswith('}'):
            try:
                content = array_data[1:-1]
                if not content.strip():
                    return []
                items = content.split(',')
                result = []
                for item in items:
                    item = item.strip()
                    if item.lower() == 'null' or item == '':
                        result.append(None)
                    else:
                        try:
                            # 숫자 변환 시도
                            if '.' in item:
                                result.append(float(item))
                            else:
                                result.append(int(item))
                        except ValueError:
                            result.append(item.strip('"\''))
                return result
            except Exception:
                pass

        return [array_data] if array_data else []

    # =========================
    # 관련 데이터 조회 메서드들
    # =========================

    async def _get_user_interaction_data(self, vehicle_ids: List[str]) -> Dict[str, Any]:
        """사용자 상호작용 데이터 조회"""
        if not vehicle_ids:
            return {}

        try:
            placeholders = ','.join(['%s'] * len(vehicle_ids))
            query = f"""
            SELECT vehicle_id, user_id, interaction_type, created_at,
                   COUNT(*) as interaction_count
            FROM user_interactions
            WHERE vehicle_id = ANY(ARRAY[{placeholders}])
            GROUP BY vehicle_id, user_id, interaction_type, created_at
            ORDER BY created_at DESC
            LIMIT 1000
            """

            df = pd.read_sql(query, self.db.engine, params=vehicle_ids)
            return {
                "interactions": df.to_dict('records'),
                "summary": {
                    "total_interactions": len(df),
                    "unique_users": df['user_id'].nunique() if not df.empty else 0,
                    "interaction_types": df['interaction_type'].value_counts().to_dict() if not df.empty else {}
                }
            }
        except Exception as e:
            logger.error(f"❌ 사용자 상호작용 데이터 조회 실패: {e}")
            return {}

    async def _get_financial_data_for_vehicles(self, vehicle_ids: List[str]) -> Dict[str, Any]:
        """차량 관련 금융 데이터 조회"""
        try:
            # 금융 상품 정보
            financial_query = """
            SELECT product_id, product_type, interest_rate, loan_term_months,
                   max_loan_amount, min_credit_score
            FROM financial_products
            WHERE is_active = true
            ORDER BY interest_rate ASC
            """

            df = pd.read_sql(financial_query, self.db.engine)
            return {
                "available_products": df.to_dict('records'),
                "summary": {
                    "product_count": len(df),
                    "avg_interest_rate": df['interest_rate'].mean() if not df.empty else 0,
                    "loan_options": df['product_type'].unique().tolist() if not df.empty else []
                }
            }
        except Exception as e:
            logger.error(f"❌ 금융 데이터 조회 실패: {e}")
            return {}

    async def _get_recommendation_history(self, vehicle_ids: List[str]) -> Dict[str, Any]:
        """추천 이력 데이터 조회"""
        if not vehicle_ids:
            return {}

        try:
            placeholders = ','.join(['%s'] * len(vehicle_ids))
            query = f"""
            SELECT vehicle_id, user_id, score, algorithm, created_at
            FROM recommendations
            WHERE vehicle_id = ANY(ARRAY[{placeholders}])
            ORDER BY created_at DESC, score DESC
            LIMIT 500
            """

            df = pd.read_sql(query, self.db.engine, params=vehicle_ids)
            return {
                "recommendation_history": df.to_dict('records'),
                "summary": {
                    "total_recommendations": len(df),
                    "avg_score": df['score'].mean() if not df.empty else 0,
                    "algorithms_used": df['algorithm'].unique().tolist() if not df.empty else []
                }
            }
        except Exception as e:
            logger.error(f"❌ 추천 이력 조회 실패: {e}")
            return {}

    async def _get_market_analysis_data(self, vehicle_ids: List[str]) -> Dict[str, Any]:
        """시장 분석 데이터 조회 (미래 테이블 - 현재는 기본값)"""
        # 미래 구현을 위한 플레이스홀더
        return {
            "market_trends": "stable",
            "price_competitiveness": "average",
            "demand_level": "moderate",
            "note": "시장 분석 테이블 추후 구현 예정"
        }

    # =========================
    # 유틸리티 메서드들
    # =========================

    def _build_filter_conditions(self, filters: Dict[str, Any]) -> Tuple[List[str], List[Any]]:
        """필터 조건을 SQL WHERE 절로 변환"""
        conditions = []
        params = []

        filter_mappings = {
            'manufacturer': 'manufacturer = %s',
            'cartype': 'cartype = %s',
            'fueltype': 'fueltype = %s',
            'location': 'location = %s',
            'selltype': 'selltype = %s'
        }

        for filter_key, condition_template in filter_mappings.items():
            if filter_key in filters and filters[filter_key]:
                conditions.append(condition_template)
                params.append(filters[filter_key])

        # 가격 범위 필터
        if 'price_min' in filters and filters['price_min']:
            conditions.append("(SELECT MIN(unnest) FROM unnest(price)) >= %s")
            params.append(filters['price_min'])

        if 'price_max' in filters and filters['price_max']:
            conditions.append("(SELECT MIN(unnest) FROM unnest(price)) <= %s")
            params.append(filters['price_max'])

        # 연식 범위 필터
        if 'year_min' in filters and filters['year_min']:
            conditions.append("(SELECT MAX(unnest) FROM unnest(modelyear)) >= %s")
            params.append(filters['year_min'])

        if 'year_max' in filters and filters['year_max']:
            conditions.append("(SELECT MAX(unnest) FROM unnest(modelyear)) <= %s")
            params.append(filters['year_max'])

        return conditions, params

    def _analyze_price_array(self, price_array: Any, origin_price_array: Any) -> Dict[str, Any]:
        """가격 ARRAY 분석"""
        prices = self._array_to_list(price_array)
        origin_prices = self._array_to_list(origin_price_array)

        if not prices:
            return {"current_price": None, "has_discount": False}

        valid_prices = [p for p in prices if p is not None and p > 0]
        if not valid_prices:
            return {"current_price": None, "has_discount": False}

        current_price = min(valid_prices)

        result = {
            "current_price": current_price,
            "price_range": {"min": min(valid_prices), "max": max(valid_prices)} if len(valid_prices) > 1 else None,
            "has_discount": False,
            "discount_percentage": 0
        }

        if origin_prices:
            valid_origins = [p for p in origin_prices if p is not None and p > 0]
            if valid_origins:
                origin_price = min(valid_origins)
                if origin_price > current_price:
                    result["has_discount"] = True
                    result["discount_percentage"] = round(((origin_price - current_price) / origin_price) * 100, 1)

        return result

    def _analyze_year_array(self, year_array: Any) -> Dict[str, Any]:
        """연식 ARRAY 분석"""
        years = self._array_to_list(year_array)

        if not years:
            return {"model_year": None, "age": None}

        valid_years = [y for y in years if y is not None and isinstance(y, (int, float))]
        if not valid_years:
            return {"model_year": None, "age": None}

        latest_year = max(valid_years)
        current_year = datetime.now().year

        return {
            "model_year": latest_year,
            "age": current_year - latest_year,
            "year_range": {"min": min(valid_years), "max": max(valid_years)} if len(valid_years) > 1 else None
        }

    def _analyze_distance_array(self, distance_array: Any) -> Dict[str, Any]:
        """주행거리 ARRAY 분석"""
        distances = self._array_to_list(distance_array)

        if not distances:
            return {"mileage": None, "condition": "unknown"}

        valid_distances = [d for d in distances if d is not None and d >= 0]
        if not valid_distances:
            return {"mileage": None, "condition": "unknown"}

        current_mileage = min(valid_distances)  # 최소 주행거리를 현재값으로

        # 주행거리 기반 상태 평가
        if current_mileage < 30000:
            condition = "excellent"
        elif current_mileage < 60000:
            condition = "good"
        elif current_mileage < 100000:
            condition = "fair"
        else:
            condition = "high_mileage"

        return {
            "mileage": current_mileage,
            "condition": condition,
            "mileage_range": {"min": min(valid_distances), "max": max(valid_distances)} if len(valid_distances) > 1 else None
        }

    def _get_array_length(self, array_data: Any) -> int:
        """ARRAY 데이터 길이 반환"""
        values = self._array_to_list(array_data)
        return len(values)

    def _calculate_data_richness(self, row_data: Dict[str, Any]) -> float:
        """데이터 풍부도 점수 계산"""
        total_fields = 22  # 전체 22개 컬럼
        filled_fields = sum(1 for v in row_data.values() if v is not None and v != '')
        return filled_fields / total_fields

    # =========================
    # 테이블 확장 지원 메서드들
    # =========================

    def register_new_table(self, table_info: TableInfo):
        """새로운 테이블 등록 (동적 확장 지원)"""
        self.table_registry[table_info.name] = table_info
        logger.info(f"✅ 새 테이블 등록됨: {table_info.name} ({table_info.category.value})")

    def get_available_tables(self, category: TableCategory = None) -> List[str]:
        """사용 가능한 테이블 목록 반환"""
        if category:
            return [name for name, info in self.table_registry.items() if info.category == category]
        return list(self.table_registry.keys())

    async def query_custom_table(self, table_name: str, query: str, params: List = None) -> pd.DataFrame:
        """커스텀 테이블 쿼리 실행"""
        if table_name not in self.table_registry:
            raise ValueError(f"테이블 '{table_name}'이 등록되지 않음")

        try:
            return pd.read_sql(query, self.db.engine, params=params)
        except Exception as e:
            logger.error(f"❌ 커스텀 쿼리 실행 실패 ({table_name}): {e}")
            raise