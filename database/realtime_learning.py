# -*- coding: utf-8 -*-
"""
실시간 학습 시스템
PostgreSQL과 통합된 실시간 사용자 행동 학습 및 추천시스템 업데이트
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import json
import numpy as np
import torch
from dataclasses import dataclass
from collections import defaultdict
import asyncpg
from .connection import DatabaseManager, UserBehaviorTracker

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class UserInteraction:
    """사용자 상호작용 데이터 클래스"""
    user_id: str
    vehicle_id: str
    interaction_type: str  # 'view', 'like', 'inquiry', 'purchase', 'compare'
    timestamp: datetime
    session_id: str
    context: Dict[str, Any]
    engagement_score: float

@dataclass
class LearningBatch:
    """실시간 학습을 위한 배치 데이터"""
    interactions: List[UserInteraction]
    batch_id: str
    created_at: datetime
    priority: int  # 1=high, 2=medium, 3=low

class RealTimeLearningEngine:
    """실시간 학습 엔진"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.behavior_tracker = UserBehaviorTracker(db_manager)
        self.learning_queue = asyncio.Queue()
        self.user_embeddings = {}
        self.vehicle_embeddings = {}
        self.learning_active = False

        # 학습 매개변수
        self.batch_size = 32
        self.learning_rate = 0.001
        self.embedding_dim = 64
        self.update_threshold = 10  # 최소 상호작용 수

    async def start_learning_pipeline(self):
        """실시간 학습 파이프라인 시작"""
        self.learning_active = True

        # 병렬 작업 시작
        tasks = [
            asyncio.create_task(self._interaction_processor()),
            asyncio.create_task(self._batch_learner()),
            asyncio.create_task(self._embedding_updater()),
            asyncio.create_task(self._preference_calculator())
        ]

        logger.info("🚀 실시간 학습 파이프라인 시작")
        await asyncio.gather(*tasks)

    async def stop_learning_pipeline(self):
        """실시간 학습 파이프라인 중지"""
        self.learning_active = False
        logger.info("⏸️ 실시간 학습 파이프라인 중지")

    async def process_user_interaction(self, interaction_data: Dict[str, Any]) -> bool:
        """사용자 상호작용 처리"""
        try:
            # 상호작용 데이터 검증
            if not self._validate_interaction(interaction_data):
                logger.warning(f"❌ 유효하지 않은 상호작용 데이터: {interaction_data}")
                return False

            # UserInteraction 객체 생성
            interaction = UserInteraction(
                user_id=interaction_data['user_id'],
                vehicle_id=interaction_data['vehicle_id'],
                interaction_type=interaction_data['interaction_type'],
                timestamp=datetime.now(),
                session_id=interaction_data.get('session_id', 'unknown'),
                context=interaction_data.get('context', {}),
                engagement_score=self._calculate_engagement_score(interaction_data)
            )

            # 즉시 데이터베이스에 저장
            await self.behavior_tracker.track_user_interaction(interaction_data)

            # 학습 큐에 추가
            await self.learning_queue.put(interaction)

            # 실시간 추천 업데이트 (고참여도 상호작용의 경우)
            if interaction.engagement_score > 0.7:
                await self._immediate_recommendation_update(interaction)

            logger.info(f"✅ 상호작용 처리 완료: {interaction.user_id} -> {interaction.vehicle_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 상호작용 처리 실패: {e}")
            return False

    async def _interaction_processor(self):
        """상호작용 처리기 (백그라운드 작업)"""
        while self.learning_active:
            try:
                # 큐에서 상호작용 가져오기 (최대 1초 대기)
                interaction = await asyncio.wait_for(
                    self.learning_queue.get(), timeout=1.0
                )

                # 상호작용 분석 및 처리
                await self._analyze_interaction(interaction)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"❌ 상호작용 처리기 오류: {e}")
                await asyncio.sleep(1)

    async def _batch_learner(self):
        """배치 학습기 (주기적 실행)"""
        while self.learning_active:
            try:
                # 5분마다 배치 학습 실행
                await asyncio.sleep(300)

                # 최근 상호작용 데이터 수집
                batch_data = await self._collect_batch_data()

                if len(batch_data) >= self.batch_size:
                    await self._execute_batch_learning(batch_data)

            except Exception as e:
                logger.error(f"❌ 배치 학습기 오류: {e}")
                await asyncio.sleep(60)

    async def _embedding_updater(self):
        """임베딩 업데이터 (주기적 업데이트)"""
        while self.learning_active:
            try:
                # 10분마다 임베딩 업데이트
                await asyncio.sleep(600)

                # 사용자 및 차량 임베딩 업데이트
                await self._update_user_embeddings()
                await self._update_vehicle_embeddings()

                logger.info("🔄 임베딩 업데이트 완료")

            except Exception as e:
                logger.error(f"❌ 임베딩 업데이터 오류: {e}")
                await asyncio.sleep(120)

    async def _preference_calculator(self):
        """선호도 계산기 (실시간 계산)"""
        while self.learning_active:
            try:
                # 2분마다 사용자 선호도 재계산
                await asyncio.sleep(120)

                # 활성 사용자들의 선호도 업데이트
                active_users = await self._get_active_users()

                for user_id in active_users:
                    await self._recalculate_user_preferences(user_id)

                logger.info(f"📊 {len(active_users)}명 사용자 선호도 업데이트 완료")

            except Exception as e:
                logger.error(f"❌ 선호도 계산기 오류: {e}")
                await asyncio.sleep(60)

    async def _analyze_interaction(self, interaction: UserInteraction):
        """상호작용 분석"""
        try:
            # 상호작용 타입별 가중치
            weights = {
                'view': 0.1,
                'like': 0.3,
                'inquiry': 0.6,
                'compare': 0.4,
                'purchase': 1.0
            }

            weight = weights.get(interaction.interaction_type, 0.1)

            # 사용자 선호도 즉시 업데이트
            await self._update_immediate_preference(
                interaction.user_id,
                interaction.vehicle_id,
                weight * interaction.engagement_score
            )

            # 차량 인기도 업데이트
            await self._update_vehicle_popularity(
                interaction.vehicle_id,
                weight
            )

        except Exception as e:
            logger.error(f"❌ 상호작용 분석 실패: {e}")

    async def _immediate_recommendation_update(self, interaction: UserInteraction):
        """즉시 추천 업데이트 (고참여도 상호작용)"""
        try:
            user_id = interaction.user_id
            vehicle_id = interaction.vehicle_id

            # 유사한 차량 찾기
            similar_vehicles = await self._find_similar_vehicles(vehicle_id)

            # 사용자의 실시간 추천 리스트 업데이트
            await self._update_user_recommendations(user_id, similar_vehicles)

            logger.info(f"⚡ 즉시 추천 업데이트: {user_id}")

        except Exception as e:
            logger.error(f"❌ 즉시 추천 업데이트 실패: {e}")

    async def _collect_batch_data(self) -> List[UserInteraction]:
        """배치 학습을 위한 데이터 수집"""
        try:
            # 최근 5분간의 상호작용 데이터 수집
            cutoff_time = datetime.now() - timedelta(minutes=5)

            query = """
                SELECT user_id, vehicle_id, interaction_type, timestamp,
                       session_id, context_data, engagement_score
                FROM user_interactions
                WHERE timestamp > $1
                ORDER BY timestamp DESC
                LIMIT 1000
            """

            async with self.db_manager.get_connection() as conn:
                rows = await conn.fetch(query, cutoff_time)

                interactions = []
                for row in rows:
                    interaction = UserInteraction(
                        user_id=row['user_id'],
                        vehicle_id=row['vehicle_id'],
                        interaction_type=row['interaction_type'],
                        timestamp=row['timestamp'],
                        session_id=row['session_id'],
                        context=json.loads(row['context_data'] or '{}'),
                        engagement_score=row['engagement_score'] or 0.5
                    )
                    interactions.append(interaction)

                return interactions

        except Exception as e:
            logger.error(f"❌ 배치 데이터 수집 실패: {e}")
            return []

    async def _execute_batch_learning(self, batch_data: List[UserInteraction]):
        """배치 학습 실행"""
        try:
            # 배치 데이터를 학습 형태로 변환
            user_ids = [int(interaction.user_id) for interaction in batch_data]
            vehicle_ids = [int(interaction.vehicle_id) for interaction in batch_data]
            ratings = [interaction.engagement_score for interaction in batch_data]

            # PyTorch 텐서로 변환
            user_tensor = torch.LongTensor(user_ids)
            vehicle_tensor = torch.LongTensor(vehicle_ids)
            rating_tensor = torch.FloatTensor(ratings)

            # 모델 로드 (기존 NCF 모델 사용)
            model = await self._load_ncf_model()

            if model:
                # 배치 학습 실행
                loss = await self._train_batch(model, user_tensor, vehicle_tensor, rating_tensor)
                logger.info(f"📚 배치 학습 완료 - Loss: {loss:.4f}")

                # 모델 저장
                await self._save_model(model)

        except Exception as e:
            logger.error(f"❌ 배치 학습 실행 실패: {e}")

    async def _update_user_embeddings(self):
        """사용자 임베딩 업데이트"""
        try:
            # 최근 활성 사용자들의 임베딩 재계산
            query = """
                SELECT DISTINCT user_id
                FROM user_interactions
                WHERE timestamp > NOW() - INTERVAL '1 hour'
            """

            async with self.db_manager.get_connection() as conn:
                rows = await conn.fetch(query)

                for row in rows:
                    user_id = row['user_id']
                    # 사용자 임베딩 재계산 로직
                    embedding = await self._calculate_user_embedding(user_id)
                    self.user_embeddings[user_id] = embedding

        except Exception as e:
            logger.error(f"❌ 사용자 임베딩 업데이트 실패: {e}")

    async def _update_vehicle_embeddings(self):
        """차량 임베딩 업데이트"""
        try:
            # 최근 상호작용이 있는 차량들의 임베딩 재계산
            query = """
                SELECT DISTINCT vehicle_id
                FROM user_interactions
                WHERE timestamp > NOW() - INTERVAL '1 hour'
            """

            async with self.db_manager.get_connection() as conn:
                rows = await conn.fetch(query)

                for row in rows:
                    vehicle_id = row['vehicle_id']
                    # 차량 임베딩 재계산 로직
                    embedding = await self._calculate_vehicle_embedding(vehicle_id)
                    self.vehicle_embeddings[vehicle_id] = embedding

        except Exception as e:
            logger.error(f"❌ 차량 임베딩 업데이트 실패: {e}")

    def _validate_interaction(self, interaction_data: Dict[str, Any]) -> bool:
        """상호작용 데이터 검증"""
        required_fields = ['user_id', 'vehicle_id', 'interaction_type']

        for field in required_fields:
            if field not in interaction_data:
                return False

        valid_types = ['view', 'like', 'inquiry', 'compare', 'purchase']
        if interaction_data['interaction_type'] not in valid_types:
            return False

        return True

    def _calculate_engagement_score(self, interaction_data: Dict[str, Any]) -> float:
        """참여도 점수 계산"""
        base_scores = {
            'view': 0.1,
            'like': 0.3,
            'inquiry': 0.7,
            'compare': 0.5,
            'purchase': 1.0
        }

        base_score = base_scores.get(interaction_data['interaction_type'], 0.1)

        # 컨텍스트 기반 가중치 적용
        context = interaction_data.get('context', {})

        # 체류 시간 가중치
        duration = context.get('duration_seconds', 10)
        duration_weight = min(duration / 60, 2.0)  # 최대 2배

        # 반복 방문 가중치
        repeat_visit = context.get('repeat_visit', False)
        repeat_weight = 1.2 if repeat_visit else 1.0

        final_score = base_score * duration_weight * repeat_weight
        return min(final_score, 1.0)  # 최대 1.0으로 제한

    async def _get_active_users(self) -> List[str]:
        """활성 사용자 목록 조회"""
        try:
            query = """
                SELECT DISTINCT user_id
                FROM user_interactions
                WHERE timestamp > NOW() - INTERVAL '10 minutes'
                LIMIT 100
            """

            async with self.db_manager.get_connection() as conn:
                rows = await conn.fetch(query)
                return [row['user_id'] for row in rows]

        except Exception as e:
            logger.error(f"❌ 활성 사용자 조회 실패: {e}")
            return []

    async def _load_ncf_model(self):
        """NCF 모델 로드"""
        try:
            # 기존 PyTorch NCF 모델 로드 로직
            model_path = "models/pytorch_ncf_real.py"
            # 실제 모델 로드 구현 필요
            return None  # 임시
        except Exception as e:
            logger.error(f"❌ NCF 모델 로드 실패: {e}")
            return None

    async def _train_batch(self, model, user_tensor, vehicle_tensor, rating_tensor):
        """배치 훈련"""
        try:
            # 실제 PyTorch 훈련 로직 구현 필요
            return 0.0  # 임시
        except Exception as e:
            logger.error(f"❌ 배치 훈련 실패: {e}")
            return float('inf')

    async def _save_model(self, model):
        """모델 저장"""
        try:
            # 모델 저장 로직 구현 필요
            pass
        except Exception as e:
            logger.error(f"❌ 모델 저장 실패: {e}")

class RealtimeRecommendationCache:
    """실시간 추천 캐시"""

    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.local_cache = {}
        self.cache_ttl = 300  # 5분

    async def get_user_recommendations(self, user_id: str) -> List[Dict]:
        """사용자 추천 조회"""
        try:
            cache_key = f"recommendations:{user_id}"

            if self.redis_client:
                # Redis에서 조회
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)

            # 로컬 캐시에서 조회
            if user_id in self.local_cache:
                cache_data = self.local_cache[user_id]
                if datetime.now() - cache_data['timestamp'] < timedelta(seconds=self.cache_ttl):
                    return cache_data['recommendations']

            return []

        except Exception as e:
            logger.error(f"❌ 추천 캐시 조회 실패: {e}")
            return []

    async def update_user_recommendations(self, user_id: str, recommendations: List[Dict]):
        """사용자 추천 업데이트"""
        try:
            cache_key = f"recommendations:{user_id}"
            recommendations_json = json.dumps(recommendations)

            if self.redis_client:
                # Redis에 저장
                await self.redis_client.setex(cache_key, self.cache_ttl, recommendations_json)

            # 로컬 캐시에 저장
            self.local_cache[user_id] = {
                'recommendations': recommendations,
                'timestamp': datetime.now()
            }

            logger.info(f"💾 추천 캐시 업데이트: {user_id}")

        except Exception as e:
            logger.error(f"❌ 추천 캐시 업데이트 실패: {e}")

# 싱글톤 인스턴스
_realtime_engine = None
_recommendation_cache = None

async def get_realtime_engine() -> RealTimeLearningEngine:
    """실시간 학습 엔진 인스턴스 조회"""
    global _realtime_engine

    if _realtime_engine is None:
        db_manager = DatabaseManager()
        _realtime_engine = RealTimeLearningEngine(db_manager)

    return _realtime_engine

async def get_recommendation_cache() -> RealtimeRecommendationCache:
    """추천 캐시 인스턴스 조회"""
    global _recommendation_cache

    if _recommendation_cache is None:
        _recommendation_cache = RealtimeRecommendationCache()

    return _recommendation_cache