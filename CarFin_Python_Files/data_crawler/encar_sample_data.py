"""
엔카 스타일 샘플 데이터 생성기
실제 엔카 중고차 매물과 유사한 데이터를 생성합니다.
"""
import os
import random
from sqlalchemy import create_engine, text
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class EncarSampleDataGenerator:
    """엔카 스타일 샘플 데이터 생성기"""
    
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL')
        if self.db_url:
            self.engine = create_engine(self.db_url)
    
    def generate_realistic_car_data(self, count: int = 100) -> list:
        """실제 엔카 매물과 유사한 차량 데이터 생성"""
        
        # 실제 한국 인기 차종 데이터
        car_models = [
            # 현대
            {'make': '현대', 'model': '아반떼', 'category': 'Sedan', 'base_price': 2500, 'fuel_efficiency': 13, 'engine_size': 1.6},
            {'make': '현대', 'model': '쏘나타', 'category': 'Sedan', 'base_price': 3200, 'fuel_efficiency': 12, 'engine_size': 2.0},
            {'make': '현대', 'model': '그랜져', 'category': 'Sedan', 'base_price': 4500, 'fuel_efficiency': 10, 'engine_size': 3.0},
            {'make': '현대', 'model': '투싼', 'category': 'SUV', 'base_price': 3800, 'fuel_efficiency': 11, 'engine_size': 2.0},
            {'make': '현대', 'model': '산타페', 'category': 'SUV', 'base_price': 4800, 'fuel_efficiency': 9, 'engine_size': 2.5},
            {'make': '현대', 'model': 'i30', 'category': 'Hatchback', 'base_price': 2800, 'fuel_efficiency': 14, 'engine_size': 1.6},
            
            # 기아
            {'make': '기아', 'model': 'K3', 'category': 'Sedan', 'base_price': 2400, 'fuel_efficiency': 13, 'engine_size': 1.6},
            {'make': '기아', 'model': 'K5', 'category': 'Sedan', 'base_price': 3300, 'fuel_efficiency': 12, 'engine_size': 2.0},
            {'make': '기아', 'model': 'K7', 'category': 'Sedan', 'base_price': 4200, 'fuel_efficiency': 11, 'engine_size': 2.5},
            {'make': '기아', 'model': '스포티지', 'category': 'SUV', 'base_price': 3600, 'fuel_efficiency': 11, 'engine_size': 2.0},
            {'make': '기아', 'model': '쏘렌토', 'category': 'SUV', 'base_price': 4600, 'fuel_efficiency': 9, 'engine_size': 2.5},
            {'make': '기아', 'model': '모닝', 'category': 'Mini', 'base_price': 1500, 'fuel_efficiency': 16, 'engine_size': 1.0},
            
            # BMW
            {'make': 'BMW', 'model': '320i', 'category': 'Sedan', 'base_price': 5500, 'fuel_efficiency': 13, 'engine_size': 2.0},
            {'make': 'BMW', 'model': '520i', 'category': 'Sedan', 'base_price': 7200, 'fuel_efficiency': 12, 'engine_size': 2.0},
            {'make': 'BMW', 'model': 'X3', 'category': 'SUV', 'base_price': 6800, 'fuel_efficiency': 10, 'engine_size': 2.0},
            {'make': 'BMW', 'model': 'X5', 'category': 'SUV', 'base_price': 9500, 'fuel_efficiency': 8, 'engine_size': 3.0},
            
            # 벤츠
            {'make': '벤츠', 'model': 'C200', 'category': 'Sedan', 'base_price': 6200, 'fuel_efficiency': 13, 'engine_size': 2.0},
            {'make': '벤츠', 'model': 'E220', 'category': 'Sedan', 'base_price': 8500, 'fuel_efficiency': 12, 'engine_size': 2.0},
            {'make': '벤츠', 'model': 'GLC', 'category': 'SUV', 'base_price': 7800, 'fuel_efficiency': 10, 'engine_size': 2.0},
            {'make': '벤츠', 'model': 'GLE', 'category': 'SUV', 'base_price': 10500, 'fuel_efficiency': 9, 'engine_size': 3.0},
            
            # 아우디
            {'make': '아우디', 'model': 'A4', 'category': 'Sedan', 'base_price': 5800, 'fuel_efficiency': 13, 'engine_size': 2.0},
            {'make': '아우디', 'model': 'A6', 'category': 'Sedan', 'base_price': 7800, 'fuel_efficiency': 11, 'engine_size': 2.0},
            {'make': '아우디', 'model': 'Q5', 'category': 'SUV', 'base_price': 6800, 'fuel_efficiency': 10, 'engine_size': 2.0},
            
            # 토요타
            {'make': '토요타', 'model': '캠리', 'category': 'Sedan', 'base_price': 3800, 'fuel_efficiency': 12, 'engine_size': 2.5},
            {'make': '토요타', 'model': 'RAV4', 'category': 'SUV', 'base_price': 4200, 'fuel_efficiency': 11, 'engine_size': 2.0},
            
            # 쉐보레
            {'make': '쉐보레', 'model': '크루즈', 'category': 'Sedan', 'base_price': 2200, 'fuel_efficiency': 14, 'engine_size': 1.4},
            {'make': '쉐보레', 'model': '트래버스', 'category': 'SUV', 'base_price': 4500, 'fuel_efficiency': 9, 'engine_size': 3.6},
        ]
        
        fuel_types = ['가솔린', '디젤', '하이브리드', 'LPG']
        transmissions = ['자동', '수동']
        
        cars_data = []
        
        for i in range(count):
            car = random.choice(car_models)
            year = random.randint(2018, 2024)
            
            # 연식에 따른 가격 조정 (감가상각)
            age = 2024 - year
            depreciation = 1 - (age * 0.12)  # 연 12% 감가상각
            price = int(car['base_price'] * depreciation * random.uniform(0.85, 1.15))  # ±15% 변동
            
            # 연료타입별 연비 조정
            fuel_type = random.choice(fuel_types)
            fuel_efficiency = car['fuel_efficiency']
            if fuel_type == '하이브리드':
                fuel_efficiency += random.randint(6, 10)
            elif fuel_type == '디젤':
                fuel_efficiency += random.randint(2, 4)
            elif fuel_type == 'LPG':
                fuel_efficiency += random.randint(1, 3)
            
            # 안전등급 (4-5점)
            safety_rating = random.choice([4, 5])
            
            cars_data.append({
                'make': car['make'],
                'model': car['model'],
                'year': year,
                'price': price,  # 만원 단위
                'fuel_type': fuel_type,
                'category': car['category'],
                'engine_size': car['engine_size'],
                'fuel_efficiency': fuel_efficiency,
                'transmission': random.choice(transmissions),
                'safety_rating': safety_rating,
                'description': f"{car['make']} {car['model']} {year}년형 - 엔카 인증 매물"
            })
        
        return cars_data
    
    def save_to_database(self, cars_data: list) -> bool:
        """데이터베이스에 저장"""
        if not self.engine or not cars_data:
            return False
            
        try:
            df = pd.DataFrame(cars_data)
            
            # 기존 데이터 삭제 후 새 데이터 추가
            with self.engine.connect() as conn:
                conn.execute(text("DELETE FROM cars WHERE id > 15"))  # 기본 15개는 유지
                conn.commit()
            
            # 새 데이터 저장
            df.to_sql('cars', self.engine, if_exists='append', index=False)
            
            logger.info(f"데이터베이스에 {len(cars_data)}개 차량 저장 완료")
            print(f"✅ {len(cars_data)}대 차량 데이터 생성 완료!")
            return True
            
        except Exception as e:
            logger.error(f"데이터베이스 저장 오류: {e}")
            print(f"❌ 데이터베이스 저장 실패: {e}")
            return False

def generate_encar_sample_data(count: int = 100):
    """엔카 샘플 데이터 생성 실행"""
    print(f"🚗 엔카 스타일 차량 데이터 {count}개 생성 중...")
    
    generator = EncarSampleDataGenerator()
    cars_data = generator.generate_realistic_car_data(count)
    
    if generator.save_to_database(cars_data):
        print(f"✅ 총 {len(cars_data)}대 차량 데이터 생성 및 저장 완료!")
        return len(cars_data)
    else:
        print("❌ 데이터 저장 실패")
        return 0

if __name__ == "__main__":
    # 직접 실행 시
    generate_encar_sample_data(80)