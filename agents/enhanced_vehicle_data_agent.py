"""
기존 Gemini 에이전트들이 22개 컬럼 ARRAY 데이터를 활용하도록 하는 데이터 레이어
VehicleDataService를 에이전트 시스템에 통합
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
import numpy as np
from dataclasses import dataclass, asdict

# 기존 에이전트 시스템과 VehicleDataService 통합
from .gemini_recommendation_agent import AgentContext, AgentRecommendation, AgentRole
from ..services.vehicle_data_service import VehicleDataService, VehicleDisplayData, VehicleApiHelper

logger = logging.getLogger(__name__)

class EnhancedVehicleDataAgent:
    """
    22개 컬럼 ARRAY 데이터를 Gemini 에이전트들에게 제공하는 데이터 레이어
    기존 추천 시스템과 새로운 차량 데이터를 연결
    """

    def __init__(self):
        self.vehicle_service = VehicleDataService()
        self.api_helper = VehicleApiHelper()

    async def get_rich_vehicle_data_for_agents(
        self,
        user_context: AgentContext,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        에이전트들이 분석할 수 있도록 22개 컬럼 데이터를 가공하여 제공
        """
        try:
            # 사용자 컨텍스트 기반 필터 생성
            filters = self._create_filters_from_context(user_context)

            # 차량 데이터 조회 (ARRAY 데이터 포함)
            vehicles = self.vehicle_service.get_vehicles_for_listing(
                filters=filters,
                limit=limit,
                offset=0
            )

            if not vehicles:
                return {
                    "vehicles": [],
                    "market_analysis": {},
                    "data_quality": "no_data",
                    "message": "조건에 맞는 차량 데이터가 없습니다"
                }

            # 에이전트들을 위한 분석 데이터 생성
            analysis_data = self._create_agent_analysis_data(vehicles, user_context)

            return {
                "vehicles": [self._convert_to_agent_format(v) for v in vehicles],
                "market_analysis": analysis_data["market_analysis"],
                "user_preference_insights": analysis_data["preference_insights"],
                "trend_analysis": analysis_data["trend_analysis"],
                "array_data_insights": analysis_data["array_insights"],
                "data_quality": "high",
                "total_vehicles": len(vehicles),
                "data_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Enhanced vehicle data 조회 실패: {e}")
            return {
                "vehicles": [],
                "market_analysis": {},
                "data_quality": "error",
                "error_message": str(e)
            }

    def _create_filters_from_context(self, context: AgentContext) -> Dict[str, Any]:
        """
        사용자 컨텍스트에서 차량 검색 필터 생성
        """
        filters = {}

        user_profile = context.user_profile

        # 사용자 선호도 기반 필터
        if user_profile.get('preferred_brands'):
            # 첫 번째 선호 브랜드 사용
            preferred_brands = user_profile['preferred_brands']
            if isinstance(preferred_brands, list) and preferred_brands:
                filters['manufacturer'] = preferred_brands[0]

        if user_profile.get('preferred_fuel_type'):
            filters['fueltype'] = user_profile['preferred_fuel_type']

        # 예산 기반 필터
        budget_range = user_profile.get('budget_range', {})
        if budget_range.get('min'):
            filters['price_min'] = budget_range['min']
        if budget_range.get('max'):
            filters['price_max'] = budget_range['max']

        # 세션 컨텍스트 기반 필터
        current_session = context.current_session
        if current_session.get('interested_cartype'):
            filters['cartype'] = current_session['interested_cartype']

        if current_session.get('preferred_location'):
            filters['location'] = current_session['preferred_location']

        return filters

    def _create_agent_analysis_data(
        self,
        vehicles: List[VehicleDisplayData],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        에이전트들이 분석할 수 있는 형태의 데이터 생성
        22개 컬럼 ARRAY 데이터의 패턴 분석 포함
        """

        # 가격 분석 (ARRAY 데이터 활용)
        price_analysis = self._analyze_price_arrays(vehicles)

        # 연식 분석 (ARRAY 데이터 활용)
        year_analysis = self._analyze_year_arrays(vehicles)

        # 주행거리 분석 (ARRAY 데이터 활용)
        mileage_analysis = self._analyze_mileage_arrays(vehicles)

        # 시장 트렌드 분석
        market_analysis = {
            "price_trends": price_analysis,
            "year_distribution": year_analysis,
            "mileage_patterns": mileage_analysis,
            "brand_distribution": self._analyze_brand_distribution(vehicles),
            "fuel_type_trends": self._analyze_fuel_trends(vehicles),
            "location_patterns": self._analyze_location_patterns(vehicles)
        }

        # 사용자 선호도 매칭 인사이트
        preference_insights = self._generate_preference_insights(vehicles, context)

        # 트렌드 분석
        trend_analysis = self._analyze_market_trends(vehicles)

        # ARRAY 데이터 특화 인사이트
        array_insights = self._analyze_array_data_patterns(vehicles)

        return {
            "market_analysis": market_analysis,
            "preference_insights": preference_insights,
            "trend_analysis": trend_analysis,
            "array_insights": array_insights
        }

    def _analyze_price_arrays(self, vehicles: List[VehicleDisplayData]) -> Dict[str, Any]:
        """가격 ARRAY 데이터 분석"""
        prices = []
        discount_info = []
        price_ranges = []

        for vehicle in vehicles:
            if vehicle.current_price:
                prices.append(vehicle.current_price)

                if vehicle.discount_info and vehicle.discount_info.get('has_discount'):
                    discount_info.append(vehicle.discount_info['percentage'])

                if vehicle.price_range:
                    range_span = vehicle.price_range['max'] - vehicle.price_range['min']
                    price_ranges.append(range_span)

        return {
            "average_price": np.mean(prices) if prices else 0,
            "price_volatility": np.std(prices) if len(prices) > 1 else 0,
            "discount_availability": len(discount_info) / len(vehicles) if vehicles else 0,
            "average_discount": np.mean(discount_info) if discount_info else 0,
            "price_range_diversity": np.mean(price_ranges) if price_ranges else 0,
            "price_segments": self._categorize_prices(prices)
        }

    def _analyze_year_arrays(self, vehicles: List[VehicleDisplayData]) -> Dict[str, Any]:
        """연식 ARRAY 데이터 분석"""
        years = []
        year_ranges = []

        for vehicle in vehicles:
            if vehicle.model_year:
                years.append(vehicle.model_year)

                if vehicle.year_range and vehicle.year_range.get('span'):
                    year_ranges.append(vehicle.year_range['span'])

        current_year = datetime.now().year

        return {
            "average_age": current_year - np.mean(years) if years else 0,
            "newest_vehicle": max(years) if years else None,
            "oldest_vehicle": min(years) if years else None,
            "year_diversity": len(set(years)) if years else 0,
            "multi_year_vehicles": len([r for r in year_ranges if r > 0]),
            "age_distribution": self._categorize_years(years, current_year)
        }

    def _analyze_mileage_arrays(self, vehicles: List[VehicleDisplayData]) -> Dict[str, Any]:
        """주행거리 ARRAY 데이터 분석"""
        mileages = []
        mileage_ranges = []

        for vehicle in vehicles:
            if vehicle.mileage:
                mileages.append(vehicle.mileage)

                if vehicle.mileage_range:
                    range_span = vehicle.mileage_range['max'] - vehicle.mileage_range['min']
                    mileage_ranges.append(range_span)

        return {
            "average_mileage": np.mean(mileages) if mileages else 0,
            "mileage_spread": np.std(mileages) if len(mileages) > 1 else 0,
            "low_mileage_count": len([m for m in mileages if m < 50000]) if mileages else 0,
            "mileage_tracking_diversity": np.mean(mileage_ranges) if mileage_ranges else 0,
            "condition_categories": self._categorize_by_mileage(mileages)
        }

    def _convert_to_agent_format(self, vehicle: VehicleDisplayData) -> Dict[str, Any]:
        """
        VehicleDisplayData를 에이전트들이 분석하기 쉬운 형태로 변환
        """
        agent_format = {
            # 기본 식별 정보
            "vehicle_id": vehicle.vehicle_id,
            "vehicle_number": vehicle.vehicle_number,

            # 에이전트 분석을 위한 핵심 정보
            "basic_info": {
                "manufacturer": vehicle.manufacturer,
                "model": vehicle.model,
                "car_type": vehicle.car_type,
                "fuel_type": vehicle.fuel_type,
                "generation": vehicle.generation,
                "trim": vehicle.trim
            },

            # 가격 분석 정보 (ARRAY 데이터 활용)
            "pricing_analysis": {
                "current_price": vehicle.current_price,
                "original_price": vehicle.original_price,
                "discount_info": vehicle.discount_info,
                "price_competitiveness": self._calculate_price_competitiveness(vehicle),
                "has_multiple_prices": bool(vehicle.price_range)
            },

            # 시간/상태 분석 정보
            "temporal_analysis": {
                "model_year": vehicle.model_year,
                "year_range": vehicle.year_range,
                "registration_info": vehicle.registration_info,
                "age_category": self._categorize_vehicle_age(vehicle.model_year),
                "has_multiple_years": bool(vehicle.year_range and vehicle.year_range.get('span', 0) > 0)
            },

            # 주행거리 분석 정보
            "mileage_analysis": {
                "current_mileage": vehicle.mileage,
                "mileage_range": vehicle.mileage_range,
                "condition_score": self._calculate_condition_score(vehicle.mileage),
                "has_multiple_records": bool(vehicle.mileage_range)
            },

            # 시장 위치 분석
            "market_position": {
                "location": vehicle.location,
                "sell_type": vehicle.sell_type,
                "platform": vehicle.platform,
                "origin": vehicle.origin
            },

            # 에이전트별 점수 계산
            "agent_scores": self._calculate_agent_scores(vehicle)
        }

        return agent_format

    def _calculate_agent_scores(self, vehicle: VehicleDisplayData) -> Dict[str, float]:
        """
        각 에이전트가 참고할 수 있는 차량별 점수 계산
        """
        scores = {}

        # 선호도 분석가용 점수
        scores["preference_match"] = self._calculate_preference_score(vehicle)

        # 시장 분석가용 점수
        scores["market_value"] = self._calculate_market_value_score(vehicle)

        # 행동 예측가용 점수
        scores["appeal_factor"] = self._calculate_appeal_score(vehicle)

        # 컨텐츠 큐레이터용 점수
        scores["content_richness"] = self._calculate_content_score(vehicle)

        # 트렌드 감지기용 점수
        scores["trend_alignment"] = self._calculate_trend_score(vehicle)

        return scores

    # 헬퍼 메서드들
    def _categorize_prices(self, prices: List[float]) -> Dict[str, int]:
        """가격 구간별 분류"""
        if not prices:
            return {}

        categories = {
            "budget": len([p for p in prices if p < 2000]),  # 2천만원 미만
            "mid_range": len([p for p in prices if 2000 <= p < 4000]),  # 2~4천만원
            "premium": len([p for p in prices if 4000 <= p < 6000]),  # 4~6천만원
            "luxury": len([p for p in prices if p >= 6000])  # 6천만원 이상
        }
        return categories

    def _categorize_years(self, years: List[int], current_year: int) -> Dict[str, int]:
        """연식별 분류"""
        if not years:
            return {}

        categories = {
            "brand_new": len([y for y in years if current_year - y <= 1]),  # 1년 이하
            "recent": len([y for y in years if 2 <= current_year - y <= 3]),  # 2-3년
            "mature": len([y for y in years if 4 <= current_year - y <= 7]),  # 4-7년
            "older": len([y for y in years if current_year - y > 7])  # 7년 이상
        }
        return categories

    def _categorize_by_mileage(self, mileages: List[float]) -> Dict[str, int]:
        """주행거리별 분류"""
        if not mileages:
            return {}

        categories = {
            "very_low": len([m for m in mileages if m < 30000]),  # 3만km 미만
            "low": len([m for m in mileages if 30000 <= m < 60000]),  # 3~6만km
            "moderate": len([m for m in mileages if 60000 <= m < 100000]),  # 6~10만km
            "high": len([m for m in mileages if m >= 100000])  # 10만km 이상
        }
        return categories

    # 추가 분석 메서드들 (간단한 구현)
    def _analyze_brand_distribution(self, vehicles: List[VehicleDisplayData]) -> Dict[str, Any]:
        brands = [v.manufacturer for v in vehicles if v.manufacturer]
        brand_counts = {}
        for brand in brands:
            brand_counts[brand] = brand_counts.get(brand, 0) + 1
        return {"distribution": brand_counts, "diversity": len(set(brands))}

    def _analyze_fuel_trends(self, vehicles: List[VehicleDisplayData]) -> Dict[str, Any]:
        fuel_types = [v.fuel_type for v in vehicles if v.fuel_type]
        fuel_counts = {}
        for fuel in fuel_types:
            fuel_counts[fuel] = fuel_counts.get(fuel, 0) + 1
        return {"distribution": fuel_counts, "eco_friendly_ratio": fuel_counts.get("하이브리드", 0) + fuel_counts.get("전기", 0)}

    def _analyze_location_patterns(self, vehicles: List[VehicleDisplayData]) -> Dict[str, Any]:
        locations = [v.location for v in vehicles if v.location]
        location_counts = {}
        for location in locations:
            location_counts[location] = location_counts.get(location, 0) + 1
        return {"distribution": location_counts, "geographic_diversity": len(set(locations))}

    def _generate_preference_insights(self, vehicles: List[VehicleDisplayData], context: AgentContext) -> Dict[str, Any]:
        # 간단한 선호도 인사이트 생성
        return {
            "matches_user_criteria": len(vehicles),
            "budget_alignment": "high",  # 실제로는 복잡한 계산 필요
            "preference_coverage": "comprehensive"
        }

    def _analyze_market_trends(self, vehicles: List[VehicleDisplayData]) -> Dict[str, Any]:
        return {
            "market_activity": "high",
            "pricing_trend": "stable",
            "inventory_level": "adequate"
        }

    def _analyze_array_data_patterns(self, vehicles: List[VehicleDisplayData]) -> Dict[str, Any]:
        return {
            "multi_price_vehicles": len([v for v in vehicles if v.price_range]),
            "multi_year_vehicles": len([v for v in vehicles if v.year_range and v.year_range.get('span', 0) > 0]),
            "data_richness_score": 0.85,
            "array_utilization": "high"
        }

    # 점수 계산 메서드들 (간단한 구현)
    def _calculate_preference_score(self, vehicle: VehicleDisplayData) -> float:
        return 0.75  # 실제로는 복잡한 계산 필요

    def _calculate_market_value_score(self, vehicle: VehicleDisplayData) -> float:
        return 0.80

    def _calculate_appeal_score(self, vehicle: VehicleDisplayData) -> float:
        return 0.70

    def _calculate_content_score(self, vehicle: VehicleDisplayData) -> float:
        return 0.85

    def _calculate_trend_score(self, vehicle: VehicleDisplayData) -> float:
        return 0.65

    def _calculate_price_competitiveness(self, vehicle: VehicleDisplayData) -> str:
        if vehicle.discount_info and vehicle.discount_info.get('has_discount', False):
            discount = vehicle.discount_info.get('percentage', 0)
            if discount > 15:
                return "매우 경쟁력 있음"
            elif discount > 5:
                return "경쟁력 있음"
        return "평균적"

    def _categorize_vehicle_age(self, model_year: Optional[int]) -> str:
        if not model_year:
            return "알 수 없음"

        age = datetime.now().year - model_year
        if age <= 1:
            return "최신"
        elif age <= 3:
            return "준신형"
        elif age <= 7:
            return "일반"
        else:
            return "구형"

    def _calculate_condition_score(self, mileage: Optional[float]) -> str:
        if not mileage:
            return "알 수 없음"

        if mileage < 30000:
            return "매우 좋음"
        elif mileage < 60000:
            return "좋음"
        elif mileage < 100000:
            return "보통"
        else:
            return "주의 필요"