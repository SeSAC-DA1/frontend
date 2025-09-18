"""
22개 컬럼 기존 구조 그대로 사용하여 웹 서비스에 효율적으로 데이터 제공
ARRAY 데이터를 사용자 친화적으로 가공하는 서비스 레이어
"""
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from config.database import DatabaseManager
import pandas as pd
import json
from datetime import datetime

@dataclass
class VehicleDisplayData:
    """프론트엔드 표시용 차량 데이터 구조"""
    # 기본 식별 정보
    vehicle_id: str
    vehicle_number: str

    # 차량 기본 정보
    manufacturer: str
    model: str
    generation: Optional[str] = None
    trim: Optional[str] = None
    car_type: str = None
    fuel_type: str = None
    transmission: str = None
    color: Optional[str] = None

    # 가격 정보 (ARRAY → 사용자 친화적 형태)
    current_price: Optional[float] = None
    original_price: Optional[float] = None
    price_range: Optional[Dict[str, float]] = None
    discount_info: Optional[Dict[str, Any]] = None

    # 연식/등록 정보 (ARRAY → 요약)
    model_year: Optional[int] = None
    year_range: Optional[Dict[str, int]] = None
    registration_info: Optional[Dict[str, Any]] = None

    # 주행거리 정보 (ARRAY → 요약)
    mileage: Optional[float] = None
    mileage_range: Optional[Dict[str, float]] = None

    # 판매 정보
    sell_type: Optional[str] = None
    location: Optional[str] = None
    platform: Optional[str] = None
    origin: Optional[str] = None

    # 미디어
    detail_url: Optional[str] = None
    photo_url: Optional[str] = None

class VehicleDataService:
    """차량 데이터 서비스 - 22개 컬럼을 웹 서비스용으로 가공"""

    def __init__(self):
        self.db = DatabaseManager()

    def get_vehicles_for_listing(self, filters: Dict[str, Any] = None, limit: int = 20, offset: int = 0) -> List[VehicleDisplayData]:
        """목록 페이지용 차량 데이터 조회 및 가공"""

        # 기본 쿼리 (22개 컬럼 그대로 조회)
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

        # 필터 조건 추가 (ARRAY 데이터 고려)
        filter_conditions = self._build_filter_conditions(filters)
        if filter_conditions:
            base_query += f" AND {filter_conditions}"

        # 정렬 및 페이징
        base_query += f" ORDER BY vehicleno LIMIT {limit} OFFSET {offset}"

        try:
            df = pd.read_sql(base_query, self.db.engine)
            vehicles = []

            for _, row in df.iterrows():
                # 각 행의 ARRAY 데이터를 가공
                vehicle_data = self._process_raw_vehicle_data(row.to_dict())
                vehicles.append(vehicle_data)

            return vehicles

        except Exception as e:
            print(f"차량 목록 조회 실패: {e}")
            return []

    def get_vehicle_detail(self, vehicle_id: str) -> Optional[VehicleDisplayData]:
        """상세 페이지용 차량 데이터 조회"""

        query = """
        SELECT
            vehicleid, carseq, vehicleno, platform, origin,
            cartype, manufacturer, model, generation, trim,
            fueltype, transmission, colorname,
            modelyear, firstregistrationdate, distance,
            price, originprice, selltype, location,
            detailurl, photo
        FROM vehicles
        WHERE vehicleno = %s OR %s = ANY(vehicleid)
        LIMIT 1
        """

        try:
            df = pd.read_sql(query, self.db.engine, params=[vehicle_id, vehicle_id])

            if len(df) == 0:
                return None

            row_data = df.iloc[0].to_dict()
            return self._process_raw_vehicle_data(row_data)

        except Exception as e:
            print(f"차량 상세 조회 실패: {e}")
            return None

    def _process_raw_vehicle_data(self, raw_data: Dict[str, Any]) -> VehicleDisplayData:
        """원본 22개 컬럼 데이터를 VehicleDisplayData로 가공"""

        # ARRAY 데이터 처리
        price_info = self._process_price_arrays(
            raw_data.get('price'),
            raw_data.get('originprice')
        )

        year_info = self._process_year_arrays(
            raw_data.get('modelyear'),
            raw_data.get('firstregistrationdate')
        )

        mileage_info = self._process_distance_array(
            raw_data.get('distance')
        )

        # vehicleid ARRAY에서 primary ID 추출
        vehicle_ids = raw_data.get('vehicleid', [])
        primary_vehicle_id = vehicle_ids[0] if vehicle_ids and len(vehicle_ids) > 0 else raw_data.get('vehicleno', 'unknown')

        return VehicleDisplayData(
            # 기본 정보
            vehicle_id=str(primary_vehicle_id),
            vehicle_number=raw_data.get('vehicleno', ''),

            # 차량 정보
            manufacturer=raw_data.get('manufacturer', ''),
            model=raw_data.get('model', ''),
            generation=raw_data.get('generation'),
            trim=raw_data.get('trim'),
            car_type=raw_data.get('cartype'),
            fuel_type=raw_data.get('fueltype'),
            transmission=raw_data.get('transmission'),
            color=raw_data.get('colorname'),

            # 가공된 가격 정보
            current_price=price_info['current_price'],
            original_price=price_info['original_price'],
            price_range=price_info['price_range'],
            discount_info=price_info['discount_info'],

            # 가공된 연식 정보
            model_year=year_info['primary_year'],
            year_range=year_info['year_range'],
            registration_info=year_info['registration_info'],

            # 가공된 주행거리 정보
            mileage=mileage_info['current_mileage'],
            mileage_range=mileage_info['mileage_range'],

            # 판매 정보
            sell_type=raw_data.get('selltype'),
            location=raw_data.get('location'),
            platform=raw_data.get('platform'),
            origin=raw_data.get('origin'),

            # 미디어
            detail_url=raw_data.get('detailurl'),
            photo_url=raw_data.get('photo')
        )

    def _process_price_arrays(self, price_array: Any, origin_price_array: Any) -> Dict[str, Any]:
        """가격 ARRAY 데이터를 사용자 친화적으로 가공"""

        # ARRAY 데이터를 리스트로 변환 (PostgreSQL ARRAY 처리)
        prices = self._safe_array_to_list(price_array)
        origin_prices = self._safe_array_to_list(origin_price_array)

        result = {
            'current_price': None,
            'original_price': None,
            'price_range': None,
            'discount_info': None
        }

        if prices:
            valid_prices = [p for p in prices if p is not None and p > 0]
            if valid_prices:
                result['current_price'] = min(valid_prices)  # 최저가격을 대표값으로

                if len(valid_prices) > 1:
                    result['price_range'] = {
                        'min': min(valid_prices),
                        'max': max(valid_prices),
                        'avg': round(sum(valid_prices) / len(valid_prices), 2)
                    }

        if origin_prices:
            valid_origin_prices = [p for p in origin_prices if p is not None and p > 0]
            if valid_origin_prices:
                result['original_price'] = min(valid_origin_prices)

        # 할인 정보 계산
        if result['current_price'] and result['original_price']:
            discount_amount = result['original_price'] - result['current_price']
            if discount_amount > 0:
                discount_percentage = round((discount_amount / result['original_price']) * 100, 1)
                result['discount_info'] = {
                    'amount': discount_amount,
                    'percentage': discount_percentage,
                    'has_discount': True
                }
            else:
                result['discount_info'] = {'has_discount': False}

        return result

    def _process_year_arrays(self, year_array: Any, registration_array: Any) -> Dict[str, Any]:
        """연식 ARRAY 데이터를 사용자 친화적으로 가공"""

        years = self._safe_array_to_list(year_array)
        registrations = self._safe_array_to_list(registration_array)

        result = {
            'primary_year': None,
            'year_range': None,
            'registration_info': None
        }

        if years:
            valid_years = [y for y in years if y is not None and isinstance(y, (int, float))]
            if valid_years:
                result['primary_year'] = max(valid_years)  # 최신 연식을 대표값으로

                if len(valid_years) > 1:
                    result['year_range'] = {
                        'min': min(valid_years),
                        'max': max(valid_years),
                        'span': max(valid_years) - min(valid_years)
                    }

        if registrations:
            valid_registrations = [r for r in registrations if r is not None]
            if valid_registrations:
                result['registration_info'] = {
                    'first_registration': min(valid_registrations),
                    'latest_registration': max(valid_registrations),
                    'registration_count': len(valid_registrations)
                }

        return result

    def _process_distance_array(self, distance_array: Any) -> Dict[str, Any]:
        """주행거리 ARRAY 데이터를 사용자 친화적으로 가공"""

        distances = self._safe_array_to_list(distance_array)

        result = {
            'current_mileage': None,
            'mileage_range': None
        }

        if distances:
            valid_distances = [d for d in distances if d is not None and d >= 0]
            if valid_distances:
                result['current_mileage'] = min(valid_distances)  # 최소 주행거리를 현재값으로

                if len(valid_distances) > 1:
                    result['mileage_range'] = {
                        'min': min(valid_distances),
                        'max': max(valid_distances),
                        'avg': round(sum(valid_distances) / len(valid_distances), 2)
                    }

        return result

    def _safe_array_to_list(self, array_data: Any) -> List[Any]:
        """PostgreSQL ARRAY 데이터를 Python 리스트로 안전하게 변환"""
        if array_data is None:
            return []

        # 이미 리스트인 경우
        if isinstance(array_data, list):
            return array_data

        # 문자열 형태의 PostgreSQL ARRAY인 경우 (예: "{1,2,3}")
        if isinstance(array_data, str):
            if array_data.startswith('{') and array_data.endswith('}'):
                try:
                    # 중괄호 제거하고 쉼표로 분리
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
                            # 숫자로 변환 시도
                            try:
                                if '.' in item:
                                    result.append(float(item))
                                else:
                                    result.append(int(item))
                            except ValueError:
                                # 문자열로 유지
                                result.append(item.strip('"\''))
                    return result
                except Exception:
                    return []

        # 단일 값인 경우 리스트로 변환
        return [array_data]

    def _build_filter_conditions(self, filters: Dict[str, Any]) -> str:
        """검색 필터를 SQL WHERE 조건으로 변환 (ARRAY 데이터 고려)"""
        if not filters:
            return ""

        conditions = []

        # 일반 텍스트 필터
        text_filters = {
            'manufacturer': 'manufacturer',
            'cartype': 'cartype',
            'fueltype': 'fueltype',
            'location': 'location',
            'selltype': 'selltype'
        }

        for filter_key, column_name in text_filters.items():
            if filter_key in filters and filters[filter_key]:
                conditions.append(f"{column_name} = '{filters[filter_key]}'")

        # 가격 범위 필터 (ARRAY 데이터 처리)
        if 'price_min' in filters or 'price_max' in filters:
            price_conditions = []

            if 'price_min' in filters and filters['price_min']:
                # ARRAY의 최소값이 price_min 이상
                price_conditions.append(f"(SELECT MIN(unnest) FROM unnest(price)) >= {filters['price_min']}")

            if 'price_max' in filters and filters['price_max']:
                # ARRAY의 최소값이 price_max 이하
                price_conditions.append(f"(SELECT MIN(unnest) FROM unnest(price)) <= {filters['price_max']}")

            if price_conditions:
                conditions.append("(" + " AND ".join(price_conditions) + ")")

        # 연식 범위 필터 (ARRAY 데이터 처리)
        if 'year_min' in filters or 'year_max' in filters:
            year_conditions = []

            if 'year_min' in filters and filters['year_min']:
                year_conditions.append(f"(SELECT MAX(unnest) FROM unnest(modelyear)) >= {filters['year_min']}")

            if 'year_max' in filters and filters['year_max']:
                year_conditions.append(f"(SELECT MAX(unnest) FROM unnest(modelyear)) <= {filters['year_max']}")

            if year_conditions:
                conditions.append("(" + " AND ".join(year_conditions) + ")")

        # 주행거리 필터 (ARRAY 데이터 처리)
        if 'distance_max' in filters and filters['distance_max']:
            conditions.append(f"(SELECT MIN(unnest) FROM unnest(distance)) <= {filters['distance_max']}")

        return " AND ".join(conditions)

# API 응답용 헬퍼 함수들
class VehicleApiHelper:
    """API 응답 최적화를 위한 헬퍼 클래스"""

    @staticmethod
    def to_api_response(vehicle: VehicleDisplayData) -> Dict[str, Any]:
        """VehicleDisplayData를 API 응답 형태로 변환"""
        return asdict(vehicle)

    @staticmethod
    def to_api_list_response(vehicles: List[VehicleDisplayData], total_count: int = None) -> Dict[str, Any]:
        """차량 목록을 API 응답 형태로 변환"""
        return {
            "vehicles": [asdict(vehicle) for vehicle in vehicles],
            "count": len(vehicles),
            "total_count": total_count,
            "has_more": total_count > len(vehicles) if total_count else False
        }

    @staticmethod
    def create_search_summary(vehicles: List[VehicleDisplayData]) -> Dict[str, Any]:
        """검색 결과 요약 정보 생성"""
        if not vehicles:
            return {"summary": "검색 결과가 없습니다"}

        prices = [v.current_price for v in vehicles if v.current_price]
        years = [v.model_year for v in vehicles if v.model_year]

        summary = {
            "total_vehicles": len(vehicles),
            "price_range": {
                "min": min(prices) if prices else None,
                "max": max(prices) if prices else None,
                "avg": round(sum(prices) / len(prices), 2) if prices else None
            },
            "year_range": {
                "min": min(years) if years else None,
                "max": max(years) if years else None
            },
            "manufacturers": list(set(v.manufacturer for v in vehicles if v.manufacturer)),
            "fuel_types": list(set(v.fuel_type for v in vehicles if v.fuel_type))
        }

        return summary