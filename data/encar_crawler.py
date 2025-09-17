"""
엔카 중고차 데이터 크롤러
실시간으로 엔카 사이트에서 중고차 정보를 수집합니다.
"""
import requests
import time
import logging
import json
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, urljoin
import random
from dataclasses import dataclass
import os
from sqlalchemy import create_engine, text
import pandas as pd

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EncarVehicle:
    """엔카 차량 정보"""
    vehicle_id: str
    make: str
    model: str
    year: int
    price: int
    mileage: int
    fuel_type: str
    category: str
    transmission: str
    location: str
    title: str
    url: str
    image_urls: List[str]
    seller_type: str
    created_at: str

class EncarCrawler:
    """엔카 크롤러"""
    
    def __init__(self):
        self.base_url = "https://www.encar.com"
        self.api_url = "https://www.encar.com/fc/service/getList.do"
        self.session = requests.Session()
        
        # User-Agent 설정 (봇 차단 방지)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.encar.com/',
            'X-Requested-With': 'XMLHttpRequest'
        })
        
        # 데이터베이스 연결
        self.db_url = os.environ.get('DATABASE_URL')
        if self.db_url:
            self.engine = create_engine(self.db_url)
        
    def get_vehicle_list(self, 
                        make: Optional[str] = None,
                        min_price: int = 0,
                        max_price: int = 50000000,
                        start_year: int = 2015,
                        page: int = 1,
                        count: int = 50) -> List[Dict]:
        """차량 목록 조회"""
        
        params = {
            'count': min(count, 50),  # 최대 50개
            'page': page,
            'sort': 'ModifiedDate',  # 최신순
            'order': 'desc',
            'fuel': '',  # 연료 타입 (빈 값은 전체)
            'carType': '',  # 차종 (빈 값은 전체)
            'bodyType': '',  # 바디 타입
            'minYear': start_year,
            'maxYear': 2024,
            'minPrice': min_price // 10000,  # 만원 단위
            'maxPrice': max_price // 10000,  # 만원 단위
        }
        
        if make:
            params['manufacturer'] = make
            
        try:
            logger.info(f"엔카 데이터 요청 중... (페이지: {page}, 브랜드: {make})")
            
            response = self.session.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            
            # JSON 응답 파싱
            data = response.json()
            
            if 'SearchResults' in data:
                vehicles = data['SearchResults']
                logger.info(f"차량 {len(vehicles)}대 조회 성공")
                return vehicles
            else:
                logger.warning("응답에서 SearchResults를 찾을 수 없음")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"네트워크 오류: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}")
            return []
        except Exception as e:
            logger.error(f"예상치 못한 오류: {e}")
            return []
    
    def parse_vehicle_data(self, raw_vehicle: Dict) -> Optional[EncarVehicle]:
        """차량 데이터 파싱"""
        try:
            # 가격 처리 (만원 → 원)
            price_str = str(raw_vehicle.get('Price', '0')).replace(',', '').replace('만원', '')
            price = int(float(price_str) * 10000) if price_str.replace('.', '').isdigit() else 0
            
            # 주행거리 처리
            mileage_str = str(raw_vehicle.get('Mileage', '0')).replace(',', '').replace('km', '')
            mileage = int(mileage_str) if mileage_str.isdigit() else 0
            
            # 연식 처리
            year_str = str(raw_vehicle.get('Year', '0')).replace('년', '')
            year = int(year_str) if year_str.isdigit() else 2020
            
            # 이미지 URL 처리
            photo_url = raw_vehicle.get('Photo', '')
            image_urls = [photo_url] if photo_url else []
            
            # 차량 정보 객체 생성
            vehicle = EncarVehicle(
                vehicle_id=str(raw_vehicle.get('Id', '')),
                make=raw_vehicle.get('Manufacturer', '').strip(),
                model=raw_vehicle.get('Model', '').strip(),
                year=year,
                price=price,
                mileage=mileage,
                fuel_type=raw_vehicle.get('FuelType', '가솔린'),
                category=self._determine_category(raw_vehicle.get('Badge', ''), raw_vehicle.get('Model', '')),
                transmission=raw_vehicle.get('Transmission', '자동'),
                location=raw_vehicle.get('Location', '서울'),
                title=f"{raw_vehicle.get('Manufacturer', '')} {raw_vehicle.get('Model', '')}",
                url=f"https://www.encar.com/dc/dc_cardetailview.do?carid={raw_vehicle.get('Id', '')}",
                image_urls=image_urls,
                seller_type=raw_vehicle.get('SellType', '일반'),
                created_at=raw_vehicle.get('RegDate', '')
            )
            
            return vehicle
            
        except Exception as e:
            logger.error(f"차량 데이터 파싱 오류: {e}")
            return None
    
    def _determine_category(self, badge: str, model: str) -> str:
        """차량 카테고리 결정"""
        badge_lower = badge.lower()
        model_lower = model.lower()
        
        if any(x in badge_lower or x in model_lower for x in ['suv', '쏘렌토', '투싼', '스포티지', 'q5', 'x3', 'glc']):
            return 'SUV'
        elif any(x in badge_lower or x in model_lower for x in ['세단', '쏘나타', '아반떼', 'k5', 'k7', '제네시스']):
            return 'Sedan'
        elif any(x in badge_lower or x in model_lower for x in ['해치백', '골프', 'i30', '벨로스터']):
            return 'Hatchback'
        elif any(x in badge_lower or x in model_lower for x in ['미니', '스파크', 'ray', '모닝']):
            return 'Mini'
        else:
            return 'Sedan'  # 기본값
    
    def crawl_vehicles(self, 
                      target_count: int = 100,
                      brands: List[str] = None) -> List[EncarVehicle]:
        """차량 데이터 크롤링"""
        
        if not brands:
            brands = ['현대', '기아', 'BMW', '벤츠', '아우디', '토요타', '쉐보레']
        
        all_vehicles = []
        vehicles_per_brand = max(1, target_count // len(brands))
        
        for brand in brands:
            logger.info(f"{brand} 브랜드 크롤링 시작...")
            brand_vehicles = []
            page = 1
            
            while len(brand_vehicles) < vehicles_per_brand and page <= 5:  # 최대 5페이지
                raw_vehicles = self.get_vehicle_list(
                    make=brand,
                    page=page,
                    count=50
                )
                
                if not raw_vehicles:
                    break
                    
                for raw_vehicle in raw_vehicles:
                    if len(brand_vehicles) >= vehicles_per_brand:
                        break
                        
                    vehicle = self.parse_vehicle_data(raw_vehicle)
                    if vehicle and vehicle.price > 0:  # 유효한 차량만
                        brand_vehicles.append(vehicle)
                
                page += 1
                time.sleep(random.uniform(1, 3))  # 요청 간격 (봇 차단 방지)
            
            all_vehicles.extend(brand_vehicles)
            logger.info(f"{brand}: {len(brand_vehicles)}대 수집 완료")
        
        logger.info(f"전체 {len(all_vehicles)}대 크롤링 완료")
        return all_vehicles
    
    def save_to_database(self, vehicles: List[EncarVehicle]) -> bool:
        """데이터베이스에 저장"""
        if not self.engine or not vehicles:
            return False
            
        try:
            # 데이터프레임으로 변환
            vehicle_data = []
            for vehicle in vehicles:
                # 안전등급은 랜덤 생성 (실제로는 크롤링으로 가져와야 함)
                safety_rating = random.randint(4, 5)
                
                # 연비 추정 (실제로는 크롤링으로 가져와야 함)
                fuel_efficiency = self._estimate_fuel_efficiency(vehicle.fuel_type, vehicle.category)
                
                vehicle_data.append({
                    'make': vehicle.make,
                    'model': vehicle.model,
                    'year': vehicle.year,
                    'price': vehicle.price // 10000,  # 만원 단위
                    'fuel_type': vehicle.fuel_type,
                    'category': vehicle.category,
                    'engine_size': 2.0,  # 기본값
                    'fuel_efficiency': fuel_efficiency,
                    'transmission': vehicle.transmission,
                    'safety_rating': safety_rating,
                    'description': f"{vehicle.make} {vehicle.model} ({vehicle.year}년, {vehicle.mileage:,}km)"
                })
            
            df = pd.DataFrame(vehicle_data)
            
            # 기존 데이터 삭제 후 새 데이터 추가
            with self.engine.connect() as conn:
                conn.execute(text("DELETE FROM cars WHERE id > 15"))  # 기본 15개는 유지
                conn.commit()
            
            # 새 데이터 저장
            df.to_sql('cars', self.engine, if_exists='append', index=False)
            
            logger.info(f"데이터베이스에 {len(vehicle_data)}개 차량 저장 완료")
            return True
            
        except Exception as e:
            logger.error(f"데이터베이스 저장 오류: {e}")
            return False
    
    def _estimate_fuel_efficiency(self, fuel_type: str, category: str) -> int:
        """연비 추정 (실제로는 크롤링 데이터 사용)"""
        base_efficiency = {
            'Sedan': 12,
            'SUV': 10,
            'Hatchback': 14,
            'Mini': 16
        }.get(category, 12)
        
        if fuel_type in ['하이브리드', 'Hybrid']:
            return base_efficiency + 8
        elif fuel_type in ['전기', 'Electric']:
            return 25  # 전기차는 특별 표기
        else:
            return base_efficiency

# 크롤러 실행 함수
def run_encar_crawler(target_count: int = 50):
    """엔카 크롤러 실행"""
    crawler = EncarCrawler()
    
    logger.info("엔카 크롤링 시작...")
    vehicles = crawler.crawl_vehicles(target_count=target_count)
    
    if vehicles:
        success = crawler.save_to_database(vehicles)
        if success:
            logger.info("✅ 엔카 크롤링 완료!")
            return len(vehicles)
        else:
            logger.error("❌ 데이터베이스 저장 실패")
            return 0
    else:
        logger.error("❌ 크롤링된 차량이 없습니다")
        return 0

if __name__ == "__main__":
    # 직접 실행 시
    count = run_encar_crawler(target_count=30)
    print(f"총 {count}대 차량 데이터 수집 완료!")