"""
AWS RDS PostgreSQL 연결 관리 시스템
실시간 사용자 행동 학습을 위한 최적화된 데이터베이스 연동
"""

import os
import asyncpg
import psycopg2
from sqlalchemy import create_engine, text, pool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
import json
import logging
from datetime import datetime, timedelta
import asyncio
from contextlib import asynccontextmanager, contextmanager
import warnings
warnings.filterwarnings('ignore')

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS RDS 연결 설정
DATABASE_CONFIG = {
    'host': 'carfin-db.cbkayiqs4div.ap-northeast-2.rds.amazonaws.com',
    'port': 5432,
    'database': 'carfin',
    'username': 'carfin_admin',
    'password': 'carfin_secure_password_2025',
    'pool_size': 20,
    'max_overflow': 30,
    'pool_timeout': 30,
    'pool_recycle': 3600,
    'echo': False  # 프로덕션에서는 False
}

# 동기/비동기 연결 URL
SYNC_DATABASE_URL = f"postgresql://{DATABASE_CONFIG['username']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
ASYNC_DATABASE_URL = f"postgresql://{DATABASE_CONFIG['username']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"

class DatabaseManager:
    """PostgreSQL 데이터베이스 연결 및 관리 클래스"""

    def __init__(self):
        self.sync_engine = None
        self.async_pool = None
        self.SessionLocal = None
        self.Base = declarative_base()
        self._initialize_sync_connection()

    def _initialize_sync_connection(self):
        """동기 연결 초기화"""
        try:
            self.sync_engine = create_engine(
                SYNC_DATABASE_URL,
                poolclass=QueuePool,
                pool_size=DATABASE_CONFIG['pool_size'],
                max_overflow=DATABASE_CONFIG['max_overflow'],
                pool_timeout=DATABASE_CONFIG['pool_timeout'],
                pool_recycle=DATABASE_CONFIG['pool_recycle'],
                pool_pre_ping=True,
                echo=DATABASE_CONFIG['echo']
            )

            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.sync_engine
            )

            logger.info("✅ 동기 PostgreSQL 연결 초기화 완료")

        except Exception as e:
            logger.error(f"❌ 동기 연결 초기화 실패: {e}")
            raise

    async def initialize_async_pool(self):
        """비동기 연결 풀 초기화"""
        try:
            self.async_pool = await asyncpg.create_pool(
                host=DATABASE_CONFIG['host'],
                port=DATABASE_CONFIG['port'],
                user=DATABASE_CONFIG['username'],
                password=DATABASE_CONFIG['password'],
                database=DATABASE_CONFIG['database'],
                min_size=5,
                max_size=20,
                command_timeout=60,
                server_settings={
                    'jit': 'off',
                    'application_name': 'CarFinanceAI'
                }
            )

            logger.info("✅ 비동기 PostgreSQL 연결 풀 초기화 완료")

        except Exception as e:
            logger.error(f"❌ 비동기 연결 풀 초기화 실패: {e}")
            raise

    def test_connection(self) -> bool:
        """데이터베이스 연결 테스트"""
        try:
            with self.sync_engine.connect() as connection:
                result = connection.execute(text("SELECT 1 as test, NOW() as timestamp"))
                row = result.fetchone()
                logger.info(f"✅ PostgreSQL 연결 성공: {row.timestamp}")
                return True
        except Exception as e:
            logger.error(f"❌ PostgreSQL 연결 실패: {e}")
            return False

    async def test_async_connection(self) -> bool:
        """비동기 연결 테스트"""
        try:
            if not self.async_pool:
                await self.initialize_async_pool()

            async with self.async_pool.acquire() as connection:
                result = await connection.fetchrow("SELECT 1 as test, NOW() as timestamp")
                logger.info(f"✅ 비동기 PostgreSQL 연결 성공: {result['timestamp']}")
                return True
        except Exception as e:
            logger.error(f"❌ 비동기 PostgreSQL 연결 실패: {e}")
            return False

    @contextmanager
    def get_db_session(self):
        """동기 데이터베이스 세션"""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    @asynccontextmanager
    async def get_async_connection(self):
        """비동기 데이터베이스 연결"""
        if not self.async_pool:
            await self.initialize_async_pool()

        async with self.async_pool.acquire() as connection:
            yield connection

    def execute_sql_file(self, sql_file_path: str):
        """SQL 파일 실행"""
        try:
            with open(sql_file_path, 'r', encoding='utf-8') as file:
                sql_content = file.read()

            # 여러 SQL 문을 분리하여 실행
            sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]

            with self.sync_engine.connect() as connection:
                for stmt in sql_statements:
                    if stmt:
                        connection.execute(text(stmt))
                connection.commit()

            logger.info(f"✅ SQL 파일 실행 완료: {sql_file_path}")

        except Exception as e:
            logger.error(f"❌ SQL 파일 실행 실패: {e}")
            raise

class UserBehaviorTracker:
    """실시간 사용자 행동 추적 및 학습 시스템"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.behavior_cache = {}  # 메모리 캐시

    async def track_user_interaction(self, interaction_data: Dict[str, Any]) -> bool:
        """사용자 상호작용 추적 (비동기)"""
        try:
            async with self.db.get_async_connection() as connection:
                # 상호작용 데이터 저장
                query = """
                INSERT INTO user_interactions
                (user_id, vehicle_id, interaction_type, rating, view_duration,
                 clicked_features, inquiry_sent, favorite_added, test_drive_requested,
                 session_id, device_type, referrer_source, implicit_score)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                RETURNING interaction_id
                """

                result = await connection.fetchrow(
                    query,
                    interaction_data.get('user_id'),
                    interaction_data.get('vehicle_id'),
                    interaction_data.get('interaction_type'),
                    interaction_data.get('rating'),
                    interaction_data.get('view_duration'),
                    json.dumps(interaction_data.get('clicked_features', [])),
                    interaction_data.get('inquiry_sent', False),
                    interaction_data.get('favorite_added', False),
                    interaction_data.get('test_drive_requested', False),
                    interaction_data.get('session_id'),
                    interaction_data.get('device_type'),
                    interaction_data.get('referrer_source'),
                    interaction_data.get('implicit_score', 1.0)
                )

                interaction_id = result['interaction_id']
                logger.info(f"✅ 상호작용 추적 완료: {interaction_id}")

                # 실시간 학습 트리거
                await self._trigger_real_time_learning(
                    interaction_data['user_id'],
                    interaction_data
                )

                return True

        except Exception as e:
            logger.error(f"❌ 상호작용 추적 실패: {e}")
            return False

    async def _trigger_real_time_learning(self, user_id: str, interaction_data: Dict):
        """실시간 학습 트리거"""
        try:
            # 사용자 선호도 업데이트
            await self._update_user_preferences(user_id, interaction_data)

            # 차량 인기도 업데이트
            await self._update_vehicle_popularity(
                interaction_data['vehicle_id'],
                interaction_data['interaction_type']
            )

            # 협업 필터링 매트릭스 업데이트 (배치 처리)
            await self._schedule_cf_update(user_id)

        except Exception as e:
            logger.error(f"❌ 실시간 학습 실패: {e}")

    async def _update_user_preferences(self, user_id: str, interaction_data: Dict):
        """사용자 선호도 실시간 업데이트"""
        try:
            # 상호작용 타입별 가중치
            interaction_weights = {
                'view': 0.1,
                'click': 0.3,
                'like': 0.5,
                'inquiry': 0.8,
                'favorite': 1.0,
                'test_drive': 1.2,
                'purchase': 2.0
            }

            weight = interaction_weights.get(interaction_data['interaction_type'], 0.1)
            vehicle_id = interaction_data['vehicle_id']

            async with self.db.get_async_connection() as connection:
                # 차량 정보 조회
                vehicle_query = """
                SELECT brand, model, fuel_type, body_type, price
                FROM vehicles
                WHERE vehicle_id = $1
                """
                vehicle_info = await connection.fetchrow(vehicle_query, vehicle_id)

                if vehicle_info:
                    # 브랜드 선호도 업데이트
                    await self._update_brand_preference(
                        connection, user_id, vehicle_info['brand'], weight
                    )

                    # 연료 타입 선호도 업데이트
                    await self._update_fuel_preference(
                        connection, user_id, vehicle_info['fuel_type'], weight
                    )

                    # 가격대 선호도 업데이트
                    await self._update_price_preference(
                        connection, user_id, vehicle_info['price'], weight
                    )

        except Exception as e:
            logger.error(f"❌ 사용자 선호도 업데이트 실패: {e}")

    async def _update_brand_preference(self, connection, user_id: str, brand: str, weight: float):
        """브랜드 선호도 업데이트"""
        query = """
        INSERT INTO user_brand_preferences (user_id, brand, preference_score, updated_at)
        VALUES ($1, $2, $3, NOW())
        ON CONFLICT (user_id, brand)
        DO UPDATE SET
            preference_score = user_brand_preferences.preference_score + $3,
            updated_at = NOW()
        """
        await connection.execute(query, user_id, brand, weight)

    async def _update_fuel_preference(self, connection, user_id: str, fuel_type: str, weight: float):
        """연료 타입 선호도 업데이트"""
        query = """
        INSERT INTO user_fuel_preferences (user_id, fuel_type, preference_score, updated_at)
        VALUES ($1, $2, $3, NOW())
        ON CONFLICT (user_id, fuel_type)
        DO UPDATE SET
            preference_score = user_fuel_preferences.preference_score + $3,
            updated_at = NOW()
        """
        await connection.execute(query, user_id, fuel_type, weight)

    async def _update_price_preference(self, connection, user_id: str, price: int, weight: float):
        """가격대 선호도 업데이트"""
        # 가격대 구간 계산
        price_range = self._get_price_range(price)

        query = """
        INSERT INTO user_price_preferences (user_id, price_range, preference_score, updated_at)
        VALUES ($1, $2, $3, NOW())
        ON CONFLICT (user_id, price_range)
        DO UPDATE SET
            preference_score = user_price_preferences.preference_score + $3,
            updated_at = NOW()
        """
        await connection.execute(query, user_id, price_range, weight)

    def _get_price_range(self, price: int) -> str:
        """가격을 구간으로 변환"""
        if price < 2000:
            return '2000만원 미만'
        elif price < 3000:
            return '2000-3000만원'
        elif price < 4000:
            return '3000-4000만원'
        elif price < 5000:
            return '4000-5000만원'
        else:
            return '5000만원 이상'

    async def _update_vehicle_popularity(self, vehicle_id: str, interaction_type: str):
        """차량 인기도 업데이트"""
        try:
            # 상호작용 타입별 인기도 점수
            popularity_scores = {
                'view': 1,
                'click': 2,
                'like': 3,
                'inquiry': 5,
                'favorite': 4,
                'test_drive': 8,
                'purchase': 10
            }

            score = popularity_scores.get(interaction_type, 1)

            async with self.db.get_async_connection() as connection:
                query = """
                INSERT INTO vehicle_popularity_scores
                (vehicle_id, popularity_score, interaction_count, updated_at)
                VALUES ($1, $2, 1, NOW())
                ON CONFLICT (vehicle_id)
                DO UPDATE SET
                    popularity_score = vehicle_popularity_scores.popularity_score + $2,
                    interaction_count = vehicle_popularity_scores.interaction_count + 1,
                    updated_at = NOW()
                """
                await connection.execute(query, vehicle_id, score)

        except Exception as e:
            logger.error(f"❌ 차량 인기도 업데이트 실패: {e}")

    async def _schedule_cf_update(self, user_id: str):
        """협업 필터링 업데이트 스케줄링"""
        # 실제로는 Redis Queue나 Celery 사용
        # 여기서는 간단히 로깅만
        logger.info(f"📊 협업 필터링 업데이트 예약: {user_id}")

    async def get_user_behavior_summary(self, user_id: str) -> Dict[str, Any]:
        """사용자 행동 요약 조회"""
        try:
            async with self.db.get_async_connection() as connection:
                # 기본 통계
                stats_query = """
                SELECT
                    COUNT(*) as total_interactions,
                    COUNT(DISTINCT vehicle_id) as unique_vehicles_viewed,
                    AVG(view_duration) as avg_view_duration,
                    COUNT(CASE WHEN inquiry_sent THEN 1 END) as inquiry_count,
                    COUNT(CASE WHEN favorite_added THEN 1 END) as favorite_count,
                    MAX(created_at) as last_interaction
                FROM user_interactions
                WHERE user_id = $1
                """

                stats = await connection.fetchrow(stats_query, user_id)

                # 브랜드 선호도
                brand_query = """
                SELECT brand, preference_score
                FROM user_brand_preferences
                WHERE user_id = $1
                ORDER BY preference_score DESC
                LIMIT 5
                """

                brand_prefs = await connection.fetch(brand_query, user_id)

                # 연료 타입 선호도
                fuel_query = """
                SELECT fuel_type, preference_score
                FROM user_fuel_preferences
                WHERE user_id = $1
                ORDER BY preference_score DESC
                """

                fuel_prefs = await connection.fetch(fuel_query, user_id)

                return {
                    'user_id': user_id,
                    'stats': dict(stats) if stats else {},
                    'brand_preferences': [dict(row) for row in brand_prefs],
                    'fuel_preferences': [dict(row) for row in fuel_prefs],
                    'last_updated': datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"❌ 사용자 행동 요약 조회 실패: {e}")
            return {}

class RecommendationDataLoader:
    """추천 시스템을 위한 데이터 로더"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def load_training_data(self) -> Dict[str, pd.DataFrame]:
        """추천 모델 훈련용 데이터 로드"""
        try:
            with self.db.get_db_session() as session:
                # 사용자-차량 상호작용 매트릭스
                interactions_query = """
                SELECT
                    ui.user_id,
                    ui.vehicle_id,
                    ui.interaction_type,
                    ui.rating,
                    ui.implicit_score,
                    ui.view_duration,
                    ui.created_at,
                    u.age,
                    u.location,
                    u.income_range,
                    v.brand,
                    v.model,
                    v.price,
                    v.fuel_type,
                    v.body_type
                FROM user_interactions ui
                JOIN users u ON ui.user_id = u.user_id
                JOIN vehicles v ON ui.vehicle_id = v.vehicle_id
                WHERE ui.created_at >= NOW() - INTERVAL '6 months'
                ORDER BY ui.created_at DESC
                """

                interactions_df = pd.read_sql(interactions_query, self.db.sync_engine)

                # 사용자 특성 데이터
                users_query = """
                SELECT
                    user_id,
                    age,
                    gender,
                    location,
                    income_range,
                    family_size,
                    preferred_brands,
                    preferred_fuel_type,
                    budget_min,
                    budget_max
                FROM users
                WHERE is_active = true
                """

                users_df = pd.read_sql(users_query, self.db.sync_engine)

                # 차량 특성 데이터
                vehicles_query = """
                SELECT
                    vehicle_id,
                    brand,
                    model,
                    year,
                    price,
                    fuel_type,
                    body_type,
                    safety_rating,
                    fuel_efficiency,
                    engine_size
                FROM vehicles
                WHERE is_active = true
                """

                vehicles_df = pd.read_sql(vehicles_query, self.db.sync_engine)

                logger.info(f"✅ 훈련 데이터 로드 완료: {len(interactions_df)} 상호작용, {len(users_df)} 사용자, {len(vehicles_df)} 차량")

                return {
                    'interactions': interactions_df,
                    'users': users_df,
                    'vehicles': vehicles_df
                }

        except Exception as e:
            logger.error(f"❌ 훈련 데이터 로드 실패: {e}")
            return {}

# 전역 인스턴스
db_manager = DatabaseManager()
user_behavior_tracker = UserBehaviorTracker(db_manager)
recommendation_data_loader = RecommendationDataLoader(db_manager)

async def initialize_database_system():
    """데이터베이스 시스템 초기화"""
    try:
        # 동기 연결 테스트
        if not db_manager.test_connection():
            raise Exception("동기 연결 실패")

        # 비동기 연결 테스트
        if not await db_manager.test_async_connection():
            raise Exception("비동기 연결 실패")

        logger.info("🎉 데이터베이스 시스템 초기화 완료!")
        return True

    except Exception as e:
        logger.error(f"❌ 데이터베이스 시스템 초기화 실패: {e}")
        return False

# 사용 예시
if __name__ == "__main__":
    async def main():
        # 시스템 초기화
        success = await initialize_database_system()

        if success:
            # 테스트 상호작용 추적
            test_interaction = {
                'user_id': 'user_001',
                'vehicle_id': 'car_001',
                'interaction_type': 'like',
                'rating': 4,
                'view_duration': 120,
                'clicked_features': ['price', 'specs'],
                'session_id': 'session_12345',
                'device_type': 'desktop',
                'implicit_score': 0.8
            }

            # 상호작용 추적
            await user_behavior_tracker.track_user_interaction(test_interaction)

            # 사용자 행동 요약 조회
            summary = await user_behavior_tracker.get_user_behavior_summary('user_001')
            print(f"사용자 행동 요약: {summary}")

    asyncio.run(main())