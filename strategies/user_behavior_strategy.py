# -*- coding: utf-8 -*-
"""
최적화된 사용자 행동 수집 전략
실시간 학습을 위한 고도화된 사용자 행동 데이터 수집 및 처리 전략
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import numpy as np
from collections import defaultdict, deque
import hashlib

# 내부 모듈
from ..database.connection import DatabaseManager
from ..database.realtime_learning import get_realtime_engine
from ..agents.gemini_recommendation_agent import get_gemini_multi_agent_system
from ..mcp.carfinance_mcp_server import get_carfinance_mcp_server

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BehaviorPriority(Enum):
    """행동 우선순위"""
    CRITICAL = 1    # 구매, 계약
    HIGH = 2        # 문의, 관심 등록
    MEDIUM = 3      # 비교, 찜하기
    LOW = 4         # 조회, 검색
    BACKGROUND = 5  # 세션 데이터, 메타데이터

class CollectionMethod(Enum):
    """수집 방법"""
    REAL_TIME = "real_time"          # 실시간 즉시 처리
    BATCH_FAST = "batch_fast"        # 1분 배치
    BATCH_REGULAR = "batch_regular"  # 5분 배치
    BATCH_SLOW = "batch_slow"        # 30분 배치
    OFFLINE = "offline"              # 오프라인 분석

@dataclass
class BehaviorEvent:
    """사용자 행동 이벤트"""
    user_id: str
    event_type: str
    timestamp: datetime
    priority: BehaviorPriority
    collection_method: CollectionMethod

    # 이벤트 데이터
    vehicle_id: Optional[str] = None
    session_id: Optional[str] = None
    page_path: Optional[str] = None
    referrer: Optional[str] = None

    # 인게이지먼트 메트릭
    duration_seconds: Optional[float] = None
    scroll_depth: Optional[float] = None
    click_count: Optional[int] = None

    # 컨텍스트 데이터
    device_type: Optional[str] = None
    browser: Optional[str] = None
    location: Optional[str] = None

    # 비즈니스 메트릭
    conversion_value: Optional[float] = None
    lead_score: Optional[float] = None

    # 메타데이터
    raw_data: Optional[Dict[str, Any]] = None

@dataclass
class CollectionRule:
    """수집 규칙"""
    event_patterns: List[str]
    priority: BehaviorPriority
    collection_method: CollectionMethod
    retention_days: int
    processing_delay_seconds: int
    batch_size: Optional[int] = None
    requires_auth: bool = False

class UserBehaviorCollectionStrategy:
    """사용자 행동 수집 전략"""

    def __init__(self):
        self.db_manager = DatabaseManager()

        # 수집 큐 (우선순위별)
        self.critical_queue = asyncio.Queue()
        self.high_priority_queue = asyncio.Queue()
        self.medium_priority_queue = asyncio.Queue()
        self.low_priority_queue = asyncio.Queue()
        self.background_queue = asyncio.Queue()

        # 배치 처리 버퍼
        self.batch_buffers = {
            CollectionMethod.BATCH_FAST: deque(maxlen=1000),
            CollectionMethod.BATCH_REGULAR: deque(maxlen=5000),
            CollectionMethod.BATCH_SLOW: deque(maxlen=20000)
        }

        # 사용자 세션 추적
        self.active_sessions = {}
        self.session_timeouts = {}

        # 실시간 메트릭
        self.metrics = {
            "events_processed": 0,
            "events_per_minute": deque(maxlen=60),
            "processing_errors": 0,
            "queue_sizes": {}
        }

        # 수집 규칙 정의
        self.collection_rules = self._define_collection_rules()

        # 처리 활성화 플래그
        self.processing_active = False

    def _define_collection_rules(self) -> Dict[str, CollectionRule]:
        """수집 규칙 정의"""
        return {
            # 🔴 CRITICAL - 즉시 처리
            "purchase": CollectionRule(
                event_patterns=["purchase_*", "contract_*", "payment_*"],
                priority=BehaviorPriority.CRITICAL,
                collection_method=CollectionMethod.REAL_TIME,
                retention_days=2555,  # 7년
                processing_delay_seconds=0,
                requires_auth=True
            ),

            "inquiry": CollectionRule(
                event_patterns=["inquiry_*", "quote_request", "contact_*"],
                priority=BehaviorPriority.CRITICAL,
                collection_method=CollectionMethod.REAL_TIME,
                retention_days=1825,  # 5년
                processing_delay_seconds=0
            ),

            # 🟠 HIGH - 1분 배치
            "engagement": CollectionRule(
                event_patterns=["like", "favorite", "save", "share"],
                priority=BehaviorPriority.HIGH,
                collection_method=CollectionMethod.BATCH_FAST,
                retention_days=365,
                processing_delay_seconds=60,
                batch_size=100
            ),

            "comparison": CollectionRule(
                event_patterns=["compare_*", "wishlist_*"],
                priority=BehaviorPriority.HIGH,
                collection_method=CollectionMethod.BATCH_FAST,
                retention_days=365,
                processing_delay_seconds=60,
                batch_size=100
            ),

            # 🟡 MEDIUM - 5분 배치
            "navigation": CollectionRule(
                event_patterns=["page_view", "search", "filter"],
                priority=BehaviorPriority.MEDIUM,
                collection_method=CollectionMethod.BATCH_REGULAR,
                retention_days=90,
                processing_delay_seconds=300,
                batch_size=500
            ),

            # 🟢 LOW - 30분 배치
            "session": CollectionRule(
                event_patterns=["session_*", "scroll", "hover"],
                priority=BehaviorPriority.LOW,
                collection_method=CollectionMethod.BATCH_SLOW,
                retention_days=30,
                processing_delay_seconds=1800,
                batch_size=2000
            ),

            # 🔵 BACKGROUND - 오프라인
            "analytics": CollectionRule(
                event_patterns=["analytics_*", "performance_*"],
                priority=BehaviorPriority.BACKGROUND,
                collection_method=CollectionMethod.OFFLINE,
                retention_days=7,
                processing_delay_seconds=3600,
                batch_size=10000
            )
        }

    async def start_collection_pipeline(self):
        """수집 파이프라인 시작"""
        self.processing_active = True

        # 병렬 처리 작업 시작
        tasks = [
            asyncio.create_task(self._critical_processor()),
            asyncio.create_task(self._high_priority_processor()),
            asyncio.create_task(self._medium_priority_processor()),
            asyncio.create_task(self._low_priority_processor()),
            asyncio.create_task(self._background_processor()),
            asyncio.create_task(self._batch_processor()),
            asyncio.create_task(self._session_manager()),
            asyncio.create_task(self._metrics_collector()),
            asyncio.create_task(self._data_quality_monitor())
        ]

        logger.info("🚀 사용자 행동 수집 파이프라인 시작")
        await asyncio.gather(*tasks)

    async def collect_behavior(self, event_data: Dict[str, Any]) -> bool:
        """사용자 행동 수집"""
        try:
            # 이벤트 분류 및 우선순위 결정
            behavior_event = await self._classify_event(event_data)

            if not behavior_event:
                return False

            # 데이터 품질 검증
            if not await self._validate_event_quality(behavior_event):
                logger.warning(f"⚠️ 데이터 품질 검증 실패: {behavior_event.event_type}")
                return False

            # 우선순위별 큐에 추가
            await self._enqueue_event(behavior_event)

            # 메트릭 업데이트
            self.metrics["events_processed"] += 1

            # 세션 추적 업데이트
            if behavior_event.session_id:
                await self._update_session_tracking(behavior_event)

            return True

        except Exception as e:
            logger.error(f"❌ 행동 수집 실패: {e}")
            self.metrics["processing_errors"] += 1
            return False

    async def _classify_event(self, event_data: Dict[str, Any]) -> Optional[BehaviorEvent]:
        """이벤트 분류"""
        try:
            event_type = event_data.get('event_type', 'unknown')

            # 수집 규칙 매칭
            rule_name, rule = self._match_collection_rule(event_type)

            if not rule:
                logger.debug(f"🔍 수집 규칙 없음: {event_type}")
                return None

            # BehaviorEvent 생성
            behavior_event = BehaviorEvent(
                user_id=event_data['user_id'],
                event_type=event_type,
                timestamp=datetime.now(),
                priority=rule.priority,
                collection_method=rule.collection_method,

                # 선택적 필드
                vehicle_id=event_data.get('vehicle_id'),
                session_id=event_data.get('session_id'),
                page_path=event_data.get('page_path'),
                referrer=event_data.get('referrer'),

                # 인게이지먼트 메트릭
                duration_seconds=event_data.get('duration_seconds'),
                scroll_depth=event_data.get('scroll_depth'),
                click_count=event_data.get('click_count'),

                # 컨텍스트
                device_type=event_data.get('device_type'),
                browser=event_data.get('browser'),
                location=event_data.get('location'),

                # 비즈니스 메트릭
                conversion_value=self._calculate_conversion_value(event_data, rule),
                lead_score=self._calculate_lead_score(event_data, rule),

                # 원본 데이터
                raw_data=event_data
            )

            return behavior_event

        except Exception as e:
            logger.error(f"❌ 이벤트 분류 실패: {e}")
            return None

    def _match_collection_rule(self, event_type: str) -> Tuple[Optional[str], Optional[CollectionRule]]:
        """수집 규칙 매칭"""
        for rule_name, rule in self.collection_rules.items():
            for pattern in rule.event_patterns:
                if pattern.endswith('*'):
                    if event_type.startswith(pattern[:-1]):
                        return rule_name, rule
                elif pattern == event_type:
                    return rule_name, rule

        return None, None

    def _calculate_conversion_value(self, event_data: Dict, rule: CollectionRule) -> float:
        """전환 가치 계산"""
        base_values = {
            BehaviorPriority.CRITICAL: 100.0,
            BehaviorPriority.HIGH: 20.0,
            BehaviorPriority.MEDIUM: 5.0,
            BehaviorPriority.LOW: 1.0,
            BehaviorPriority.BACKGROUND: 0.1
        }

        base_value = base_values.get(rule.priority, 1.0)

        # 컨텍스트 기반 가중치
        multiplier = 1.0

        if event_data.get('repeat_visitor'):
            multiplier *= 1.5

        if event_data.get('premium_user'):
            multiplier *= 2.0

        if event_data.get('duration_seconds', 0) > 300:  # 5분 이상
            multiplier *= 1.3

        return base_value * multiplier

    def _calculate_lead_score(self, event_data: Dict, rule: CollectionRule) -> float:
        """리드 점수 계산"""
        score = 0.0

        # 우선순위 기반 점수
        priority_scores = {
            BehaviorPriority.CRITICAL: 50,
            BehaviorPriority.HIGH: 20,
            BehaviorPriority.MEDIUM: 10,
            BehaviorPriority.LOW: 5,
            BehaviorPriority.BACKGROUND: 1
        }

        score += priority_scores.get(rule.priority, 1)

        # 행동 패턴 기반 추가 점수
        if 'purchase' in event_data.get('event_type', ''):
            score += 100
        elif 'inquiry' in event_data.get('event_type', ''):
            score += 50
        elif 'compare' in event_data.get('event_type', ''):
            score += 15

        # 참여도 기반 점수
        duration = event_data.get('duration_seconds', 0)
        if duration > 600:  # 10분 이상
            score += 20
        elif duration > 300:  # 5분 이상
            score += 10
        elif duration > 60:  # 1분 이상
            score += 5

        return min(score, 100.0)  # 최대 100점

    async def _validate_event_quality(self, event: BehaviorEvent) -> bool:
        """이벤트 품질 검증"""
        # 필수 필드 검증
        if not event.user_id or not event.event_type:
            return False

        # 타임스탬프 검증 (미래 시간 또는 너무 과거 시간 제외)
        now = datetime.now()
        if event.timestamp > now + timedelta(minutes=5):
            return False
        if event.timestamp < now - timedelta(days=1):
            return False

        # 사용자 ID 형식 검증
        if not self._is_valid_user_id(event.user_id):
            return False

        # 중복 이벤트 검증 (동일한 사용자의 동일한 이벤트가 1초 내 중복)
        if await self._is_duplicate_event(event):
            return False

        return True

    def _is_valid_user_id(self, user_id: str) -> bool:
        """사용자 ID 유효성 검증"""
        if not user_id or len(user_id) < 3:
            return False

        # 테스트 사용자 제외
        test_patterns = ['test_', 'demo_', 'admin_', 'system_']
        if any(user_id.startswith(pattern) for pattern in test_patterns):
            return False

        return True

    async def _is_duplicate_event(self, event: BehaviorEvent) -> bool:
        """중복 이벤트 검증"""
        # 간단한 해시 기반 중복 검증
        event_hash = hashlib.md5(
            f"{event.user_id}_{event.event_type}_{event.timestamp.strftime('%Y%m%d%H%M%S')}".encode()
        ).hexdigest()

        # 실제로는 Redis나 메모리 캐시를 사용하여 최근 이벤트 해시를 저장
        # 여기서는 간단히 구현
        return False

    async def _enqueue_event(self, event: BehaviorEvent):
        """우선순위별 큐에 이벤트 추가"""
        priority_queues = {
            BehaviorPriority.CRITICAL: self.critical_queue,
            BehaviorPriority.HIGH: self.high_priority_queue,
            BehaviorPriority.MEDIUM: self.medium_priority_queue,
            BehaviorPriority.LOW: self.low_priority_queue,
            BehaviorPriority.BACKGROUND: self.background_queue
        }

        queue = priority_queues.get(event.priority)
        if queue:
            await queue.put(event)

    async def _critical_processor(self):
        """Critical 우선순위 처리기 (즉시 처리)"""
        while self.processing_active:
            try:
                event = await asyncio.wait_for(self.critical_queue.get(), timeout=1.0)
                await self._process_event_immediately(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"❌ Critical 처리기 오류: {e}")

    async def _high_priority_processor(self):
        """High 우선순위 처리기 (1분 배치)"""
        while self.processing_active:
            try:
                await asyncio.sleep(60)  # 1분 대기
                events = []

                # 큐에서 이벤트 수집 (최대 100개)
                for _ in range(100):
                    try:
                        event = self.high_priority_queue.get_nowait()
                        events.append(event)
                    except asyncio.QueueEmpty:
                        break

                if events:
                    await self._process_events_batch(events)

            except Exception as e:
                logger.error(f"❌ High priority 처리기 오류: {e}")

    async def _medium_priority_processor(self):
        """Medium 우선순위 처리기 (5분 배치)"""
        while self.processing_active:
            try:
                await asyncio.sleep(300)  # 5분 대기
                events = []

                # 큐에서 이벤트 수집 (최대 500개)
                for _ in range(500):
                    try:
                        event = self.medium_priority_queue.get_nowait()
                        events.append(event)
                    except asyncio.QueueEmpty:
                        break

                if events:
                    await self._process_events_batch(events)

            except Exception as e:
                logger.error(f"❌ Medium priority 처리기 오류: {e}")

    async def _low_priority_processor(self):
        """Low 우선순위 처리기 (30분 배치)"""
        while self.processing_active:
            try:
                await asyncio.sleep(1800)  # 30분 대기
                events = []

                # 큐에서 이벤트 수집 (최대 2000개)
                for _ in range(2000):
                    try:
                        event = self.low_priority_queue.get_nowait()
                        events.append(event)
                    except asyncio.QueueEmpty:
                        break

                if events:
                    await self._process_events_batch(events)

            except Exception as e:
                logger.error(f"❌ Low priority 처리기 오류: {e}")

    async def _background_processor(self):
        """Background 처리기 (1시간 배치)"""
        while self.processing_active:
            try:
                await asyncio.sleep(3600)  # 1시간 대기
                events = []

                # 큐에서 이벤트 수집 (모든 이벤트)
                while True:
                    try:
                        event = self.background_queue.get_nowait()
                        events.append(event)
                    except asyncio.QueueEmpty:
                        break

                if events:
                    await self._process_events_offline(events)

            except Exception as e:
                logger.error(f"❌ Background 처리기 오류: {e}")

    async def _process_event_immediately(self, event: BehaviorEvent):
        """이벤트 즉시 처리"""
        try:
            # 실시간 학습 엔진에 전달
            engine = await get_realtime_engine()

            interaction_data = {
                "user_id": event.user_id,
                "vehicle_id": event.vehicle_id,
                "interaction_type": event.event_type,
                "context": {
                    "session_id": event.session_id,
                    "duration_seconds": event.duration_seconds,
                    "conversion_value": event.conversion_value,
                    "lead_score": event.lead_score
                }
            }

            success = await engine.process_user_interaction(interaction_data)

            if success:
                logger.info(f"⚡ 즉시 처리 완료: {event.event_type} for {event.user_id}")
            else:
                logger.warning(f"⚠️ 즉시 처리 실패: {event.event_type} for {event.user_id}")

        except Exception as e:
            logger.error(f"❌ 즉시 처리 오류: {e}")

    async def _process_events_batch(self, events: List[BehaviorEvent]):
        """이벤트 배치 처리"""
        try:
            if not events:
                return

            # 데이터베이스 배치 삽입
            await self._batch_insert_events(events)

            # 고가치 이벤트는 추가 처리
            high_value_events = [e for e in events if e.conversion_value > 50]

            for event in high_value_events:
                await self._process_event_immediately(event)

            logger.info(f"📦 배치 처리 완료: {len(events)}개 이벤트")

        except Exception as e:
            logger.error(f"❌ 배치 처리 오류: {e}")

    async def _batch_insert_events(self, events: List[BehaviorEvent]):
        """이벤트 배치 삽입"""
        try:
            if not events:
                return

            # 배치 삽입 SQL
            insert_query = """
                INSERT INTO user_interactions
                (user_id, vehicle_id, interaction_type, timestamp, session_id,
                 context_data, engagement_score, conversion_value, lead_score)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """

            # 데이터 준비
            batch_data = []
            for event in events:
                context_data = {
                    "page_path": event.page_path,
                    "referrer": event.referrer,
                    "duration_seconds": event.duration_seconds,
                    "scroll_depth": event.scroll_depth,
                    "click_count": event.click_count,
                    "device_type": event.device_type,
                    "browser": event.browser,
                    "location": event.location
                }

                batch_data.append((
                    event.user_id,
                    event.vehicle_id,
                    event.event_type,
                    event.timestamp,
                    event.session_id,
                    json.dumps(context_data),
                    event.conversion_value or 0.0,
                    event.conversion_value or 0.0,
                    event.lead_score or 0.0
                ))

            # 배치 실행
            async with self.db_manager.get_connection() as conn:
                await conn.executemany(insert_query, batch_data)

            logger.info(f"💾 배치 삽입 완료: {len(batch_data)}개")

        except Exception as e:
            logger.error(f"❌ 배치 삽입 실패: {e}")

    async def get_collection_metrics(self) -> Dict[str, Any]:
        """수집 메트릭 조회"""
        current_time = datetime.now()

        # 큐 크기 업데이트
        self.metrics["queue_sizes"] = {
            "critical": self.critical_queue.qsize(),
            "high": self.high_priority_queue.qsize(),
            "medium": self.medium_priority_queue.qsize(),
            "low": self.low_priority_queue.qsize(),
            "background": self.background_queue.qsize()
        }

        # 분당 처리율 계산
        events_per_minute = len(self.metrics["events_per_minute"])

        return {
            "total_events_processed": self.metrics["events_processed"],
            "processing_errors": self.metrics["processing_errors"],
            "events_per_minute": events_per_minute,
            "queue_sizes": self.metrics["queue_sizes"],
            "active_sessions": len(self.active_sessions),
            "collection_rules": len(self.collection_rules),
            "processing_active": self.processing_active,
            "timestamp": current_time.isoformat()
        }

# 싱글톤 인스턴스
_collection_strategy = None

async def get_user_behavior_collection_strategy() -> UserBehaviorCollectionStrategy:
    """사용자 행동 수집 전략 인스턴스 조회"""
    global _collection_strategy

    if _collection_strategy is None:
        _collection_strategy = UserBehaviorCollectionStrategy()

    return _collection_strategy