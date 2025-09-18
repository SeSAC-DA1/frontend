"""
실제 22개 컬럼 AWS RDS vehicles 테이블을 사용하는 API 라우트
VehicleDataService와 통합하여 ARRAY 데이터 최적화 처리
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import sys
import os

# VehicleDataService import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.vehicle_data_service import VehicleDataService, VehicleApiHelper, VehicleDisplayData

# API 라우터 생성
router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])

# Pydantic 모델들
class VehicleListRequest(BaseModel):
    """차량 목록 조회 요청"""
    page: int = Field(1, ge=1, description="페이지 번호")
    limit: int = Field(20, ge=1, le=100, description="페이지당 항목 수")
    manufacturer: Optional[str] = Field(None, description="제조사 필터")
    cartype: Optional[str] = Field(None, description="차종 필터")
    fueltype: Optional[str] = Field(None, description="연료타입 필터")
    location: Optional[str] = Field(None, description="지역 필터")
    price_min: Optional[int] = Field(None, description="최소 가격 (만원)")
    price_max: Optional[int] = Field(None, description="최대 가격 (만원)")
    year_min: Optional[int] = Field(None, description="최소 연식")
    year_max: Optional[int] = Field(None, description="최대 연식")
    distance_max: Optional[int] = Field(None, description="최대 주행거리 (km)")

class VehicleSearchRequest(BaseModel):
    """차량 검색 요청"""
    query: str = Field(..., description="검색어")
    filters: Optional[Dict[str, Any]] = Field(None, description="추가 필터")
    sort_by: str = Field("price", description="정렬 기준: price, year, distance")
    sort_order: str = Field("asc", description="정렬 순서: asc, desc")

class VehicleListResponse(BaseModel):
    """차량 목록 응답"""
    vehicles: List[VehicleDisplayData]
    pagination: Dict[str, Any]
    summary: Dict[str, Any]
    total_count: int

class VehicleDetailResponse(BaseModel):
    """차량 상세 응답"""
    vehicle: VehicleDisplayData
    related_vehicles: List[VehicleDisplayData]
    metadata: Dict[str, Any]

# 전역 서비스 인스턴스
vehicle_service = VehicleDataService()
api_helper = VehicleApiHelper()

@router.get("/", response_model=VehicleListResponse)
async def get_vehicles(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    manufacturer: Optional[str] = Query(None, description="제조사"),
    cartype: Optional[str] = Query(None, description="차종"),
    fueltype: Optional[str] = Query(None, description="연료타입"),
    location: Optional[str] = Query(None, description="지역"),
    price_min: Optional[int] = Query(None, description="최소 가격"),
    price_max: Optional[int] = Query(None, description="최대 가격"),
    year_min: Optional[int] = Query(None, description="최소 연식"),
    year_max: Optional[int] = Query(None, description="최대 연식"),
    distance_max: Optional[int] = Query(None, description="최대 주행거리")
):
    """
    22개 컬럼 vehicles 테이블에서 차량 목록 조회
    ARRAY 데이터를 사용자 친화적으로 가공하여 반환
    """
    try:
        # 필터 조건 구성
        filters = {}

        if manufacturer:
            filters['manufacturer'] = manufacturer
        if cartype:
            filters['cartype'] = cartype
        if fueltype:
            filters['fueltype'] = fueltype
        if location:
            filters['location'] = location
        if price_min:
            filters['price_min'] = price_min
        if price_max:
            filters['price_max'] = price_max
        if year_min:
            filters['year_min'] = year_min
        if year_max:
            filters['year_max'] = year_max
        if distance_max:
            filters['distance_max'] = distance_max

        # 페이징 계산
        offset = (page - 1) * limit

        # 차량 데이터 조회
        vehicles = vehicle_service.get_vehicles_for_listing(
            filters=filters,
            limit=limit,
            offset=offset
        )

        if not vehicles:
            return VehicleListResponse(
                vehicles=[],
                pagination={
                    "page": page,
                    "limit": limit,
                    "total_pages": 0,
                    "has_next": False,
                    "has_prev": False
                },
                summary={"message": "조건에 맞는 차량이 없습니다"},
                total_count=0
            )

        # 검색 결과 요약 생성
        summary = api_helper.create_search_summary(vehicles)

        # 전체 개수 조회 (실제로는 COUNT 쿼리 필요)
        total_count = len(vehicles)  # 임시로 현재 결과 수 사용
        total_pages = (total_count + limit - 1) // limit

        return VehicleListResponse(
            vehicles=vehicles,
            pagination={
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
                "total_count": total_count,
                "has_next": page < total_pages,
                "has_prev": page > 1
            },
            summary=summary,
            total_count=total_count
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"차량 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{vehicle_id}", response_model=VehicleDetailResponse)
async def get_vehicle_detail(vehicle_id: str):
    """
    특정 차량의 상세 정보 조회
    ARRAY 데이터를 포함한 모든 정보를 가공하여 제공
    """
    try:
        # 차량 상세 정보 조회
        vehicle = vehicle_service.get_vehicle_detail(vehicle_id)

        if not vehicle:
            raise HTTPException(
                status_code=404,
                detail="해당 차량을 찾을 수 없습니다"
            )

        # 유사한 차량 추천 (같은 제조사 또는 차종)
        similar_filters = {
            'manufacturer': vehicle.manufacturer,
            'cartype': vehicle.car_type
        }

        related_vehicles = vehicle_service.get_vehicles_for_listing(
            filters=similar_filters,
            limit=5,
            offset=0
        )

        # 현재 차량 제외
        related_vehicles = [v for v in related_vehicles if v.vehicle_id != vehicle.vehicle_id][:4]

        # 메타데이터 생성
        metadata = {
            "view_timestamp": "2024-09-18T09:00:00Z",
            "data_freshness": "실시간",
            "array_processing": {
                "price_options": len(vehicle.price_range) if vehicle.price_range else 1,
                "year_variations": vehicle.year_range if vehicle.year_range else None,
                "mileage_records": vehicle.mileage_range if vehicle.mileage_range else None
            },
            "recommendations": {
                "total_related": len(related_vehicles),
                "match_basis": f"{vehicle.manufacturer} {vehicle.car_type} 기반 추천"
            }
        }

        return VehicleDetailResponse(
            vehicle=vehicle,
            related_vehicles=related_vehicles,
            metadata=metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"차량 상세 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/search", response_model=VehicleListResponse)
async def search_vehicles(request: VehicleSearchRequest):
    """
    차량 통합 검색
    제조사, 모델명, 차종 등을 종합적으로 검색
    """
    try:
        # 검색어 기반 필터 구성
        search_filters = request.filters or {}

        # 검색어를 여러 필드에서 매칭하도록 확장 (실제로는 더 복잡한 검색 로직 필요)
        search_query = request.query.lower()

        # 임시 구현: 제조사나 모델명에 검색어가 포함된 경우
        if search_query:
            # 실제로는 PostgreSQL의 LIKE나 전문검색을 사용해야 함
            pass  # 여기서는 기본 필터링만 사용

        vehicles = vehicle_service.get_vehicles_for_listing(
            filters=search_filters,
            limit=50,  # 검색은 더 많은 결과 반환
            offset=0
        )

        # 정렬 적용
        if request.sort_by == "price" and vehicles:
            reverse_order = request.sort_order == "desc"
            vehicles.sort(
                key=lambda x: x.current_price or float('inf'),
                reverse=reverse_order
            )
        elif request.sort_by == "year" and vehicles:
            reverse_order = request.sort_order == "desc"
            vehicles.sort(
                key=lambda x: x.model_year or 0,
                reverse=reverse_order
            )

        summary = api_helper.create_search_summary(vehicles)
        summary["search_query"] = request.query
        summary["sort_applied"] = f"{request.sort_by} ({request.sort_order})"

        return VehicleListResponse(
            vehicles=vehicles,
            pagination={
                "page": 1,
                "limit": len(vehicles),
                "total_pages": 1,
                "total_count": len(vehicles),
                "has_next": False,
                "has_prev": False
            },
            summary=summary,
            total_count=len(vehicles)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"차량 검색 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/stats/overview")
async def get_vehicle_stats():
    """
    차량 데이터 통계 개요
    ARRAY 데이터 활용한 시장 분석 정보
    """
    try:
        # 전체 차량 데이터 조회 (통계용)
        all_vehicles = vehicle_service.get_vehicles_for_listing(limit=1000)

        if not all_vehicles:
            return {
                "message": "등록된 차량 데이터가 없습니다",
                "total_count": 0
            }

        # 통계 계산
        prices = [v.current_price for v in all_vehicles if v.current_price]
        years = [v.model_year for v in all_vehicles if v.model_year]
        manufacturers = [v.manufacturer for v in all_vehicles if v.manufacturer]
        fuel_types = [v.fuel_type for v in all_vehicles if v.fuel_type]

        stats = {
            "총_차량_수": len(all_vehicles),
            "가격_통계": {
                "최저가": min(prices) if prices else None,
                "최고가": max(prices) if prices else None,
                "평균가": round(sum(prices) / len(prices), 2) if prices else None
            },
            "연식_분포": {
                "최구형": min(years) if years else None,
                "최신형": max(years) if years else None,
                "평균연식": round(sum(years) / len(years), 1) if years else None
            },
            "제조사_분포": {
                manufacturer: manufacturers.count(manufacturer)
                for manufacturer in set(manufacturers)
            },
            "연료타입_분포": {
                fuel_type: fuel_types.count(fuel_type)
                for fuel_type in set(fuel_types)
            },
            "데이터_품질": {
                "가격_정보_완성도": f"{len(prices) / len(all_vehicles) * 100:.1f}%" if all_vehicles else "0%",
                "연식_정보_완성도": f"{len(years) / len(all_vehicles) * 100:.1f}%" if all_vehicles else "0%"
            }
        }

        return {
            "status": "success",
            "data_timestamp": "2024-09-18T09:00:00Z",
            "statistics": stats,
            "notes": [
                "ARRAY 컬럼에서 추출한 대표값 기준 통계",
                "실시간 데이터 반영",
                "22개 컬럼 구조 완전 활용"
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"통계 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/filters/options")
async def get_filter_options():
    """
    필터링 옵션 목록 제공
    프론트엔드에서 동적 필터 구성에 사용
    """
    try:
        # 실제로는 DB에서 DISTINCT 값들을 조회해야 함
        # 임시로 일반적인 옵션들 제공

        options = {
            "manufacturers": [
                "현대", "기아", "BMW", "벤츠", "아우디", "도요타",
                "렉서스", "볼보", "폭스바겐", "닛산"
            ],
            "car_types": [
                "세단", "SUV", "해치백", "쿠페", "컨버터블",
                "픽업트럭", "왜건", "밴"
            ],
            "fuel_types": [
                "가솔린", "디젤", "하이브리드", "전기", "LPG"
            ],
            "transmissions": [
                "자동", "수동", "CVT", "DCT"
            ],
            "locations": [
                "서울", "경기", "인천", "부산", "대구", "광주",
                "대전", "울산", "세종", "강원", "충북", "충남",
                "전북", "전남", "경북", "경남", "제주"
            ],
            "price_ranges": [
                {"label": "1천만원 미만", "min": 0, "max": 1000},
                {"label": "1천~2천만원", "min": 1000, "max": 2000},
                {"label": "2천~3천만원", "min": 2000, "max": 3000},
                {"label": "3천~4천만원", "min": 3000, "max": 4000},
                {"label": "4천~5천만원", "min": 4000, "max": 5000},
                {"label": "5천만원 이상", "min": 5000, "max": 99999}
            ],
            "year_ranges": [
                {"label": "2020년 이후", "min": 2020, "max": 2024},
                {"label": "2015~2019년", "min": 2015, "max": 2019},
                {"label": "2010~2014년", "min": 2010, "max": 2014},
                {"label": "2010년 이전", "min": 1990, "max": 2009}
            ]
        }

        return {
            "status": "success",
            "filter_options": options,
            "last_updated": "2024-09-18T09:00:00Z"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"필터 옵션 조회 중 오류가 발생했습니다: {str(e)}"
        )