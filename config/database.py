"""
AWS RDS PostgreSQL 연결 설정
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd
from typing import Dict, List, Any
import logging

# 데이터베이스 연결 설정
DATABASE_CONFIG = {
    'host': 'carfin-db.cbkayiqs4div.ap-northeast-2.rds.amazonaws.com',
    'port': 5432,
    'database': 'carfin',
    'username': 'carfin_admin',
    'password': 'carfin_secure_password_2025'
}

# SQLAlchemy 설정
DATABASE_URL = f"postgresql://{DATABASE_CONFIG['username']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False  # 프로덕션에서는 False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

logger = logging.getLogger(__name__)

class DatabaseManager:
    """데이터베이스 연결 및 데이터 관리 클래스"""

    def __init__(self):
        self.engine = engine

    def test_connection(self) -> bool:
        """데이터베이스 연결 테스트"""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                logger.info("✅ PostgreSQL 연결 성공!")
                return True
        except Exception as e:
            logger.error(f"❌ PostgreSQL 연결 실패: {e}")
            return False

    def execute_sql_file(self, sql_file_path: str):
        """SQL 파일 실행"""
        try:
            with open(sql_file_path, 'r', encoding='utf-8') as file:
                sql_content = file.read()

            with self.engine.connect() as connection:
                connection.execute(text(sql_content))
                connection.commit()

            logger.info(f"✅ SQL 파일 실행 완료: {sql_file_path}")

        except Exception as e:
            logger.error(f"❌ SQL 파일 실행 실패: {e}")
            raise

    def load_vehicles_data(self) -> pd.DataFrame:
        """차량 데이터 조회"""
        query = """
        SELECT
            vehicle_id,
            brand,
            model,
            year,
            price,
            fuel_type,
            transmission,
            mileage,
            engine_size,
            fuel_efficiency,
            safety_rating,
            body_type,
            color,
            location,
            seller_type,
            accident_history,
            owner_count,
            maintenance_records,
            created_at,
            updated_at
        FROM vehicles
        WHERE is_active = true
        ORDER BY created_at DESC
        """

        try:
            df = pd.read_sql(query, self.engine)
            logger.info(f"✅ 차량 데이터 로드 완료: {len(df)}건")
            return df
        except Exception as e:
            logger.error(f"❌ 차량 데이터 로드 실패: {e}")
            return pd.DataFrame()

    def load_users_data(self) -> pd.DataFrame:
        """사용자 데이터 조회"""
        query = """
        SELECT
            user_id,
            name,
            email,
            age,
            gender,
            location,
            income_range,
            occupation,
            family_size,
            driving_experience,
            preferred_brands,
            preferred_fuel_type,
            budget_min,
            budget_max,
            created_at,
            last_active_at
        FROM users
        WHERE is_active = true
        """

        try:
            df = pd.read_sql(query, self.engine)
            logger.info(f"✅ 사용자 데이터 로드 완료: {len(df)}건")
            return df
        except Exception as e:
            logger.error(f"❌ 사용자 데이터 로드 실패: {e}")
            return pd.DataFrame()

    def load_interactions_data(self) -> pd.DataFrame:
        """사용자-차량 상호작용 데이터 조회"""
        query = """
        SELECT
            interaction_id,
            user_id,
            vehicle_id,
            interaction_type,
            rating,
            view_duration,
            clicked_features,
            inquiry_sent,
            favorite_added,
            test_drive_requested,
            created_at,
            session_id,
            device_type,
            referrer_source
        FROM user_interactions
        WHERE created_at >= NOW() - INTERVAL '6 months'
        ORDER BY created_at DESC
        """

        try:
            df = pd.read_sql(query, self.engine)
            logger.info(f"✅ 상호작용 데이터 로드 완료: {len(df)}건")
            return df
        except Exception as e:
            logger.error(f"❌ 상호작용 데이터 로드 실패: {e}")
            return pd.DataFrame()

    def load_market_data(self) -> pd.DataFrame:
        """시장 데이터 조회 (가격 변동, 인기도 등)"""
        query = """
        SELECT
            vehicle_id,
            brand,
            model,
            avg_market_price,
            price_trend_30d,
            view_count_7d,
            inquiry_count_7d,
            popularity_score,
            depreciation_rate,
            resale_value_score,
            updated_at
        FROM market_analytics
        WHERE updated_at >= NOW() - INTERVAL '30 days'
        """

        try:
            df = pd.read_sql(query, self.engine)
            logger.info(f"✅ 시장 데이터 로드 완료: {len(df)}건")
            return df
        except Exception as e:
            logger.error(f"❌ 시장 데이터 로드 실패: {e}")
            return pd.DataFrame()

    def insert_recommendations_log(self, recommendations_data: List[Dict[str, Any]]):
        """추천 결과 로그 저장"""
        try:
            df = pd.DataFrame(recommendations_data)
            df.to_sql('recommendation_logs', self.engine, if_exists='append', index=False)
            logger.info(f"✅ 추천 로그 저장 완료: {len(df)}건")
        except Exception as e:
            logger.error(f"❌ 추천 로그 저장 실패: {e}")

    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """사용자 선호도 업데이트"""
        try:
            query = text("""
            UPDATE users
            SET
                preferred_brands = :preferred_brands,
                preferred_fuel_type = :preferred_fuel_type,
                budget_min = :budget_min,
                budget_max = :budget_max,
                last_preference_update = NOW()
            WHERE user_id = :user_id
            """)

            with self.engine.connect() as connection:
                connection.execute(query, {
                    'user_id': user_id,
                    'preferred_brands': preferences.get('brands'),
                    'preferred_fuel_type': preferences.get('fuel_type'),
                    'budget_min': preferences.get('budget_min'),
                    'budget_max': preferences.get('budget_max')
                })
                connection.commit()

            logger.info(f"✅ 사용자 선호도 업데이트 완료: {user_id}")

        except Exception as e:
            logger.error(f"❌ 사용자 선호도 업데이트 실패: {e}")

# 전역 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager()

def get_database():
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()