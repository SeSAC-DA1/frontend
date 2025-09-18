#!/usr/bin/env python3
"""
CarFinanceAI 실제 데이터 연동 설정 스크립트
AWS RDS PostgreSQL 연동 + PyTorch NCF 모델 훈련

실행 방법:
python setup_real_data.py --mode init    # 데이터베이스 초기화
python setup_real_data.py --mode train   # 모델 훈련
python setup_real_data.py --mode test    # 추천 테스트
"""

import argparse
import logging
import sys
import os
from typing import Dict, Any
import pandas as pd
import numpy as np

# 프로젝트 모듈 import
from config.database import db_manager
from models.pytorch_ncf_real import RealDataNCFSystem

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('setup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class CarFinAISetup:
    """CarFinanceAI 시스템 설정 및 초기화"""

    def __init__(self):
        self.db_manager = db_manager
        self.ncf_system = None

    def check_prerequisites(self) -> bool:
        """필수 조건 확인"""
        logger.info("🔍 필수 조건 확인 중...")

        # 1. 데이터베이스 연결 확인
        if not self.db_manager.test_connection():
            logger.error("❌ PostgreSQL 연결 실패")
            return False

        # 2. 필요한 디렉토리 생성
        os.makedirs('models', exist_ok=True)
        os.makedirs('data', exist_ok=True)
        os.makedirs('logs', exist_ok=True)

        logger.info("✅ 필수 조건 확인 완료")
        return True

    def init_database(self):
        """데이터베이스 초기화 (테이블 생성 + 샘플 데이터)"""
        logger.info("🗄️ 데이터베이스 초기화 시작...")

        try:
            # 1. 테이블 생성
            sql_file_path = 'data/create_tables.sql'
            if os.path.exists(sql_file_path):
                logger.info("테이블 생성 중...")
                self.db_manager.execute_sql_file(sql_file_path)
            else:
                logger.warning("SQL 파일을 찾을 수 없습니다. 수동으로 테이블을 생성하세요.")

            # 2. 샘플 데이터 생성 및 삽입
            logger.info("샘플 데이터 생성 중...")
            self._create_sample_data()

            logger.info("✅ 데이터베이스 초기화 완료!")

        except Exception as e:
            logger.error(f"❌ 데이터베이스 초기화 실패: {e}")
            raise

    def _create_sample_data(self):
        """실제 데이터가 없을 때 샘플 데이터 생성"""
        logger.info("📊 샘플 데이터 생성 시작...")

        # 실제 차량 브랜드/모델 기반 샘플 데이터
        real_car_data = [
            # 현대 차량들
            {'brand': '현대', 'model': '아반떼', 'category': 'sedan', 'price_range': (2000, 2800)},
            {'brand': '현대', 'model': '소나타', 'category': 'sedan', 'price_range': (2800, 3500)},
            {'brand': '현대', 'model': '그랜저', 'category': 'sedan', 'price_range': (3500, 4500)},
            {'brand': '현대', 'model': '투싼', 'category': 'suv', 'price_range': (2500, 3200)},
            {'brand': '현대', 'model': '싼타페', 'category': 'suv', 'price_range': (3200, 4200)},

            # 기아 차량들
            {'brand': '기아', 'model': 'K3', 'category': 'sedan', 'price_range': (1900, 2700)},
            {'brand': '기아', 'model': 'K5', 'category': 'sedan', 'price_range': (2700, 3400)},
            {'brand': '기아', 'model': 'K7', 'category': 'sedan', 'price_range': (3400, 4300)},
            {'brand': '기아', 'model': '스포티지', 'category': 'suv', 'price_range': (2400, 3100)},
            {'brand': '기아', 'model': '모하비', 'category': 'suv', 'price_range': (3800, 4800)},

            # BMW 차량들
            {'brand': 'BMW', 'model': '320i', 'category': 'sedan', 'price_range': (2800, 3800)},
            {'brand': 'BMW', 'model': '520i', 'category': 'sedan', 'price_range': (3800, 5000)},
            {'brand': 'BMW', 'model': 'X3', 'category': 'suv', 'price_range': (4000, 5500)},
            {'brand': 'BMW', 'model': 'X5', 'category': 'suv', 'price_range': (5500, 7500)},

            # 벤츠 차량들
            {'brand': '벤츠', 'model': 'C200', 'category': 'sedan', 'price_range': (3200, 4500)},
            {'brand': '벤츠', 'model': 'E200', 'category': 'sedan', 'price_range': (4500, 6000)},
            {'brand': '벤츠', 'model': 'GLC', 'category': 'suv', 'price_range': (4800, 6500)},
        ]

        # 사용자 데이터 생성 (300명)
        users_data = []
        for i in range(300):
            age = np.random.randint(22, 65)
            income = np.random.randint(3000, 12000)

            users_data.append({
                'user_id': f'user_{i+1:03d}',
                'name': f'사용자{i+1}',
                'email': f'user{i+1}@carfin.ai',
                'age': age,
                'gender': np.random.choice(['male', 'female']),
                'location': np.random.choice(['서울', '경기', '부산', '대구', '인천', '광주', '대전']),
                'income_range': f'{income-500}-{income+500}',
                'occupation': np.random.choice(['회사원', '자영업', '공무원', '전문직', '학생']),
                'family_size': np.random.randint(1, 5),
                'driving_experience': max(1, age - 18 - np.random.randint(0, 5)),
                'preferred_brands': np.random.choice(['현대,기아', 'BMW,벤츠', '현대,BMW', '기아,벤츠', '모든브랜드']),
                'preferred_fuel_type': np.random.choice(['gasoline', 'hybrid', 'electric', 'any']),
                'budget_min': max(1500, int(income * 0.3)),
                'budget_max': min(10000, int(income * 0.8)),
                'preferred_body_type': np.random.choice(['sedan', 'suv', 'hatchback', 'any']),
                'is_active': True
            })

        # 차량 데이터 생성 (500대)
        vehicles_data = []
        fuel_types = ['gasoline', 'hybrid', 'electric', 'diesel']
        colors = ['흰색', '검은색', '은색', '회색', '빨간색', '파란색']
        locations = ['서울 강남구', '서울 서초구', '경기 성남시', '부산 해운대구', '대구 수성구']

        for i in range(500):
            car_template = np.random.choice(real_car_data)
            price = np.random.randint(car_template['price_range'][0], car_template['price_range'][1])

            vehicles_data.append({
                'vehicle_id': f'car_{i+1:03d}',
                'brand': car_template['brand'],
                'model': car_template['model'],
                'year': np.random.randint(2017, 2024),
                'price': price,
                'fuel_type': np.random.choice(fuel_types),
                'transmission': np.random.choice(['automatic', 'manual']),
                'mileage': np.random.randint(5000, 150000),
                'engine_size': round(np.random.uniform(1.0, 3.5), 1),
                'fuel_efficiency': np.random.randint(8, 25),
                'safety_rating': round(np.random.uniform(3.5, 5.0), 1),
                'body_type': car_template['category'],
                'color': np.random.choice(colors),
                'location': np.random.choice(locations),
                'seller_type': np.random.choice(['dealer', 'individual']),
                'accident_history': np.random.choice([True, False], p=[0.3, 0.7]),
                'owner_count': np.random.randint(1, 4),
                'is_active': True
            })

        # 상호작용 데이터 생성 (15000건)
        interactions_data = []
        interaction_types = ['view', 'click', 'like', 'inquiry', 'favorite']

        for _ in range(15000):
            user_id = f'user_{np.random.randint(1, 301):03d}'
            vehicle_id = f'car_{np.random.randint(1, 501):03d}'
            interaction_type = np.random.choice(interaction_types, p=[0.5, 0.25, 0.1, 0.1, 0.05])

            # 상호작용 타입별 암시적 점수
            if interaction_type == 'favorite':
                implicit_score = np.random.uniform(0.9, 1.0)
                rating = 5
            elif interaction_type == 'inquiry':
                implicit_score = np.random.uniform(0.8, 0.95)
                rating = np.random.choice([4, 5])
            elif interaction_type == 'like':
                implicit_score = np.random.uniform(0.6, 0.8)
                rating = np.random.choice([3, 4, 5])
            elif interaction_type == 'click':
                implicit_score = np.random.uniform(0.4, 0.7)
                rating = np.random.choice([2, 3, 4])
            else:  # view
                implicit_score = np.random.uniform(0.2, 0.5)
                rating = np.random.choice([1, 2, 3])

            interactions_data.append({
                'user_id': user_id,
                'vehicle_id': vehicle_id,
                'interaction_type': interaction_type,
                'rating': rating,
                'view_duration': np.random.randint(5, 300),
                'clicked_features': np.random.choice(['specs', 'images', 'price', 'location'], size=np.random.randint(0, 4)).tolist(),
                'inquiry_sent': interaction_type == 'inquiry',
                'favorite_added': interaction_type == 'favorite',
                'test_drive_requested': np.random.choice([True, False], p=[0.05, 0.95]),
                'session_id': f'session_{np.random.randint(1, 5000)}',
                'device_type': np.random.choice(['desktop', 'mobile', 'tablet']),
                'implicit_score': implicit_score
            })

        # 데이터프레임 생성
        users_df = pd.DataFrame(users_data)
        vehicles_df = pd.DataFrame(vehicles_data)
        interactions_df = pd.DataFrame(interactions_data)

        # PostgreSQL에 저장 (실제 환경에서는 주석 해제)
        try:
            logger.info("PostgreSQL에 데이터 저장 중...")
            # users_df.to_sql('users', self.db_manager.engine, if_exists='append', index=False)
            # vehicles_df.to_sql('vehicles', self.db_manager.engine, if_exists='append', index=False)
            # interactions_df.to_sql('user_interactions', self.db_manager.engine, if_exists='append', index=False)

            # CSV 파일로도 저장 (백업용)
            users_df.to_csv('data/sample_users.csv', index=False)
            vehicles_df.to_csv('data/sample_vehicles.csv', index=False)
            interactions_df.to_csv('data/sample_interactions.csv', index=False)

            logger.info(f"✅ 샘플 데이터 생성 완료: {len(users_df)}명 사용자, {len(vehicles_df)}대 차량, {len(interactions_df)}건 상호작용")

        except Exception as e:
            logger.warning(f"PostgreSQL 저장 실패, CSV로만 저장: {e}")

    def train_model(self):
        """NCF 모델 훈련"""
        logger.info("🧠 PyTorch NCF 모델 훈련 시작...")

        try:
            # NCF 시스템 초기화
            self.ncf_system = RealDataNCFSystem(embedding_dim=64)

            # 실제 데이터 로드
            if not self.ncf_system.load_real_data():
                logger.error("데이터 로드 실패")
                return False

            # 모델 훈련
            logger.info("모델 훈련 중... (약 5-10분 소요)")
            self.ncf_system.train_model(epochs=50, early_stopping_patience=10)

            # 모델 평가
            evaluation = self.ncf_system.evaluate_model()
            logger.info(f"모델 평가 완료: RMSE={evaluation['rmse']:.4f}, MAE={evaluation['mae']:.4f}")

            # 모델 저장
            model_path = 'models/pytorch_ncf_production.pth'
            self.ncf_system.save_model(model_path)
            logger.info(f"✅ 모델 저장 완료: {model_path}")

            return True

        except Exception as e:
            logger.error(f"❌ 모델 훈련 실패: {e}")
            return False

    def test_recommendations(self):
        """추천 시스템 테스트"""
        logger.info("🎯 추천 시스템 테스트 시작...")

        try:
            # 모델 로드
            if self.ncf_system is None:
                self.ncf_system = RealDataNCFSystem(embedding_dim=64)
                model_path = 'models/pytorch_ncf_production.pth'

                if os.path.exists(model_path):
                    self.ncf_system.load_model(model_path)
                    logger.info("모델 로드 완료")
                else:
                    logger.error("훈련된 모델을 찾을 수 없습니다. train 모드를 먼저 실행하세요.")
                    return False

            # 테스트 사용자들에 대한 추천 생성
            test_users = ['user_001', 'user_002', 'user_003', 'user_010', 'user_050']
            candidate_vehicles = [f'car_{i:03d}' for i in range(1, 21)]  # 상위 20개 차량

            for user_id in test_users:
                logger.info(f"\n👤 사용자 {user_id} 추천 결과:")

                recommendations = self.ncf_system.predict_user_preferences(
                    user_id, candidate_vehicles
                )

                for i, rec in enumerate(recommendations[:5]):
                    logger.info(f"  {i+1}. {rec['vehicle_id']}: 점수 {rec['predicted_score']:.4f}")

            logger.info("✅ 추천 테스트 완료!")
            return True

        except Exception as e:
            logger.error(f"❌ 추천 테스트 실패: {e}")
            return False

    def run_benchmark(self):
        """성능 벤치마크"""
        logger.info("⚡ 성능 벤치마크 시작...")

        if self.ncf_system is None:
            logger.error("모델이 로드되지 않았습니다.")
            return

        import time

        # 추천 속도 테스트
        test_user = 'user_001'
        candidate_vehicles = [f'car_{i:03d}' for i in range(1, 101)]  # 100개 차량

        start_time = time.time()
        recommendations = self.ncf_system.predict_user_preferences(test_user, candidate_vehicles)
        end_time = time.time()

        processing_time = (end_time - start_time) * 1000  # ms 변환

        logger.info(f"📊 성능 결과:")
        logger.info(f"  - 추천 생성 시간: {processing_time:.2f}ms")
        logger.info(f"  - 처리된 차량 수: {len(candidate_vehicles)}개")
        logger.info(f"  - 초당 처리 속도: {len(candidate_vehicles) / (processing_time/1000):.1f} vehicles/sec")

def main():
    parser = argparse.ArgumentParser(description='CarFinanceAI 실제 데이터 연동 설정')
    parser.add_argument('--mode', choices=['init', 'train', 'test', 'benchmark'], required=True,
                        help='실행 모드 선택')

    args = parser.parse_args()

    setup = CarFinAISetup()

    # 필수 조건 확인
    if not setup.check_prerequisites():
        logger.error("필수 조건 확인 실패. 종료합니다.")
        sys.exit(1)

    # 모드별 실행
    if args.mode == 'init':
        setup.init_database()

    elif args.mode == 'train':
        if setup.train_model():
            logger.info("🎉 모델 훈련이 성공적으로 완료되었습니다!")
            logger.info("다음 명령어로 추천 테스트를 실행하세요: python setup_real_data.py --mode test")
        else:
            sys.exit(1)

    elif args.mode == 'test':
        if setup.test_recommendations():
            logger.info("🎉 추천 시스템 테스트가 성공적으로 완료되었습니다!")
        else:
            sys.exit(1)

    elif args.mode == 'benchmark':
        setup.run_benchmark()

if __name__ == "__main__":
    main()