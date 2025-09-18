# -*- coding: utf-8 -*-
"""
Gemini 멀티에이전트 추천시스템 통합
실시간 학습과 연동되는 AI 에이전트 시스템
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict
from enum import Enum
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor
import numpy as np

# 데이터베이스 및 실시간 학습 모듈
from ..database.connection import DatabaseManager
from ..database.realtime_learning import get_realtime_engine, get_recommendation_cache

# 22개 컬럼 ARRAY 데이터 처리를 위한 Enhanced 에이전트
from .enhanced_vehicle_data_agent import EnhancedVehicleDataAgent

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentRole(Enum):
    """에이전트 역할 정의"""
    PREFERENCE_ANALYZER = "preference_analyzer"     # 선호도 분석가
    MARKET_ANALYST = "market_analyst"              # 시장 분석가
    BEHAVIOR_PREDICTOR = "behavior_predictor"      # 행동 예측가
    CONTENT_CURATOR = "content_curator"            # 컨텐츠 큐레이터
    TREND_SPOTTER = "trend_spotter"                # 트렌드 감지기
    DECISION_SYNTHESIZER = "decision_synthesizer"   # 결정 종합가

@dataclass
class AgentContext:
    """에이전트 컨텍스트"""
    user_id: str
    user_profile: Dict[str, Any]
    interaction_history: List[Dict]
    current_session: Dict[str, Any]
    market_context: Dict[str, Any]
    timestamp: datetime

@dataclass
class AgentRecommendation:
    """에이전트 추천 결과"""
    agent_role: AgentRole
    recommendations: List[Dict[str, Any]]
    confidence_score: float
    reasoning: str
    supporting_data: Dict[str, Any]
    priority: int

class GeminiAgent:
    """개별 Gemini 에이전트"""

    def __init__(self, role: AgentRole, api_key: str, model_name: str = "gemini-1.5-pro"):
        self.role = role
        self.model_name = model_name
        self.client = genai.GenerativeModel(model_name)

        # 역할별 전문화된 프롬프트
        self.system_prompts = {
            AgentRole.PREFERENCE_ANALYZER: self._get_preference_analyzer_prompt(),
            AgentRole.MARKET_ANALYST: self._get_market_analyst_prompt(),
            AgentRole.BEHAVIOR_PREDICTOR: self._get_behavior_predictor_prompt(),
            AgentRole.CONTENT_CURATOR: self._get_content_curator_prompt(),
            AgentRole.TREND_SPOTTER: self._get_trend_spotter_prompt(),
            AgentRole.DECISION_SYNTHESIZER: self._get_decision_synthesizer_prompt()
        }

    async def analyze(self, context: AgentContext) -> AgentRecommendation:
        """컨텍스트 분석 및 추천 생성"""
        try:
            # 역할별 전문화된 분석 수행
            prompt = self._build_analysis_prompt(context)

            # Gemini API 호출
            response = await self._call_gemini_api(prompt)

            # 응답 파싱 및 구조화
            recommendation = self._parse_response(response, context)

            logger.info(f"✅ {self.role.value} 분석 완료 - 신뢰도: {recommendation.confidence_score:.2f}")
            return recommendation

        except Exception as e:
            logger.error(f"❌ {self.role.value} 분석 실패: {e}")
            return self._create_fallback_recommendation(context)

    def _build_analysis_prompt(self, context: AgentContext) -> str:
        """역할별 분석 프롬프트 구성"""
        base_prompt = self.system_prompts[self.role]

        user_data = {
            "user_id": context.user_id,
            "profile": context.user_profile,
            "recent_interactions": context.interaction_history[-20:],  # 최근 20개
            "session_data": context.current_session,
            "market_context": context.market_context
        }

        context_prompt = f"""
사용자 컨텍스트:
{json.dumps(user_data, ensure_ascii=False, indent=2)}

현재 시각: {context.timestamp.isoformat()}

분석 요청:
{self.role.value}의 역할로서 위 컨텍스트를 분석하고 추천을 제공해주세요.
응답은 반드시 JSON 형태로 제공해주세요.
"""

        return base_prompt + "\n\n" + context_prompt

    async def _call_gemini_api(self, prompt: str) -> str:
        """Gemini API 호출"""
        try:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                response = await loop.run_in_executor(
                    executor,
                    lambda: self.client.generate_content(prompt)
                )
                return response.text
        except Exception as e:
            logger.error(f"❌ Gemini API 호출 실패: {e}")
            raise

    def _parse_response(self, response: str, context: AgentContext) -> AgentRecommendation:
        """Gemini 응답 파싱"""
        try:
            # JSON 응답 파싱
            response_data = json.loads(response)

            return AgentRecommendation(
                agent_role=self.role,
                recommendations=response_data.get('recommendations', []),
                confidence_score=response_data.get('confidence_score', 0.5),
                reasoning=response_data.get('reasoning', ''),
                supporting_data=response_data.get('supporting_data', {}),
                priority=response_data.get('priority', 3)
            )

        except json.JSONDecodeError:
            logger.warning(f"⚠️ JSON 파싱 실패, 텍스트 응답 처리: {self.role.value}")
            return self._parse_text_response(response, context)

    def _create_fallback_recommendation(self, context: AgentContext) -> AgentRecommendation:
        """실패 시 기본 추천"""
        return AgentRecommendation(
            agent_role=self.role,
            recommendations=[],
            confidence_score=0.1,
            reasoning="에이전트 분석 실패로 인한 기본 응답",
            supporting_data={},
            priority=5
        )

    # 역할별 프롬프트 정의
    def _get_preference_analyzer_prompt(self) -> str:
        return """
당신은 자동차 추천시스템의 선호도 분석 전문가입니다.

주요 역할:
1. 사용자의 과거 행동 패턴 분석
2. 명시적/암시적 선호도 추출
3. 선호도 변화 트렌드 감지
4. 개인화된 차량 속성 중요도 계산

분석 항목:
- 차량 브랜드, 모델, 가격대 선호도
- 연료 타입, 차체 형태 선호도
- 색상, 옵션 선호도
- 구매 시점 예측

응답 형식:
{
  "recommendations": [
    {
      "vehicle_id": "차량ID",
      "preference_match_score": 0.95,
      "key_attributes": ["속성1", "속성2"],
      "reasoning": "선호도 매칭 근거"
    }
  ],
  "confidence_score": 0.85,
  "reasoning": "전체 분석 근거",
  "supporting_data": {
    "preference_trends": {},
    "attribute_weights": {}
  },
  "priority": 1
}
"""

    def _get_market_analyst_prompt(self) -> str:
        return """
당신은 자동차 시장 분석 전문가입니다.

주요 역할:
1. 현재 자동차 시장 트렌드 분석
2. 가격 동향 및 경쟁력 평가
3. 지역별/계절별 수요 패턴 분석
4. 재고 상황 및 할인 혜택 분석

분석 항목:
- 시장 인기 차량 순위
- 가격 경쟁력 분석
- 계절성 및 지역성 고려
- 프로모션 및 할인 정보

응답은 동일한 JSON 형식으로 제공해주세요.
"""

    def _get_behavior_predictor_prompt(self) -> str:
        return """
당신은 사용자 행동 예측 전문가입니다.

주요 역할:
1. 구매 행동 패턴 예측
2. 다음 관심 차량 예측
3. 구매 시점 예측
4. 이탈 위험도 평가

분석 항목:
- 구매 의도 강도 측정
- 비교 검토 패턴 분석
- 세션 내 행동 시퀀스 분석
- 이탈 방지 액션 제안

응답은 동일한 JSON 형식으로 제공해주세요.
"""

    def _get_content_curator_prompt(self) -> str:
        return """
당신은 자동차 컨텐츠 큐레이션 전문가입니다.

주요 역할:
1. 맞춤형 차량 정보 제공
2. 비교 컨텐츠 생성
3. 리뷰 및 평점 큐레이션
4. 관련 뉴스 및 정보 제공

분석 항목:
- 사용자 관심사에 맞는 컨텐츠
- 차량 비교 가이드
- 전문가 리뷰 추천
- 관련 뉴스 및 트렌드

응답은 동일한 JSON 형식으로 제공해주세요.
"""

    def _get_trend_spotter_prompt(self) -> str:
        return """
당신은 자동차 트렌드 감지 전문가입니다.

주요 역할:
1. 신규 트렌드 감지
2. 사용자 그룹별 트렌드 분석
3. 계절성 트렌드 파악
4. 미래 트렌드 예측

분석 항목:
- 인기 상승 차량 감지
- 사용자층별 트렌드 차이
- 계절성 패턴 인식
- 트렌드 지속성 예측

응답은 동일한 JSON 형식으로 제공해주세요.
"""

    def _get_decision_synthesizer_prompt(self) -> str:
        return """
당신은 추천 결정 종합 전문가입니다.

주요 역할:
1. 다중 에이전트 결과 종합
2. 최종 추천 우선순위 결정
3. 신뢰도 가중평균 계산
4. 추천 근거 통합 설명

분석 항목:
- 에이전트별 추천 일치도
- 신뢰도 기반 가중치 적용
- 최종 추천 리스트 구성
- 통합 추천 근거 제시

응답은 동일한 JSON 형식으로 제공해주세요.
"""

class GeminiMultiAgentSystem:
    """Gemini 멀티에이전트 시스템"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)

        # 에이전트 초기화
        self.agents = {
            role: GeminiAgent(role, api_key)
            for role in AgentRole if role != AgentRole.DECISION_SYNTHESIZER
        }

        # 결정 종합 에이전트 (별도 처리)
        self.synthesizer = GeminiAgent(AgentRole.DECISION_SYNTHESIZER, api_key)

        # 데이터베이스 매니저
        self.db_manager = DatabaseManager()

    async def get_recommendations(self, user_id: str, context_data: Dict = None) -> Dict[str, Any]:
        """통합 추천 생성"""
        try:
            # 사용자 컨텍스트 구성
            context = await self._build_context(user_id, context_data)

            # 병렬 에이전트 분석 실행
            agent_tasks = [
                agent.analyze(context)
                for agent in self.agents.values()
            ]

            agent_results = await asyncio.gather(*agent_tasks, return_exceptions=True)

            # 에러 제외하고 유효한 결과만 필터링
            valid_results = [
                result for result in agent_results
                if isinstance(result, AgentRecommendation)
            ]

            # 결과 종합
            final_recommendations = await self._synthesize_recommendations(
                valid_results, context
            )

            # 실시간 캐시 업데이트
            cache = await get_recommendation_cache()
            await cache.update_user_recommendations(user_id, final_recommendations['recommendations'])

            logger.info(f"🎯 멀티에이전트 추천 완료: {user_id}")
            return final_recommendations

        except Exception as e:
            logger.error(f"❌ 멀티에이전트 추천 실패: {e}")
            return await self._get_fallback_recommendations(user_id)

    async def _build_context(self, user_id: str, context_data: Dict = None) -> AgentContext:
        """사용자 컨텍스트 구성"""
        try:
            # 사용자 프로필 조회
            user_profile = await self._get_user_profile(user_id)

            # 상호작용 히스토리 조회
            interaction_history = await self._get_interaction_history(user_id)

            # 현재 세션 정보
            current_session = context_data or {}

            # 시장 컨텍스트 구성
            market_context = await self._get_market_context()

            return AgentContext(
                user_id=user_id,
                user_profile=user_profile,
                interaction_history=interaction_history,
                current_session=current_session,
                market_context=market_context,
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"❌ 컨텍스트 구성 실패: {e}")
            raise

    async def _synthesize_recommendations(self, agent_results: List[AgentRecommendation], context: AgentContext) -> Dict[str, Any]:
        """에이전트 결과 종합"""
        try:
            # 종합 프롬프트 구성
            synthesis_data = {
                "agent_recommendations": [asdict(result) for result in agent_results],
                "context": asdict(context)
            }

            # 결정 종합 에이전트 실행
            synthesis_context = AgentContext(
                user_id=context.user_id,
                user_profile=context.user_profile,
                interaction_history=[],  # 종합에는 불필요
                current_session={"synthesis_data": synthesis_data},
                market_context=context.market_context,
                timestamp=context.timestamp
            )

            synthesized_result = await self.synthesizer.analyze(synthesis_context)

            # 최종 추천 구성
            final_recommendations = {
                "recommendations": synthesized_result.recommendations,
                "confidence_score": synthesized_result.confidence_score,
                "reasoning": synthesized_result.reasoning,
                "agent_contributions": {
                    result.agent_role.value: {
                        "confidence": result.confidence_score,
                        "priority": result.priority,
                        "count": len(result.recommendations)
                    }
                    for result in agent_results
                },
                "timestamp": datetime.now().isoformat(),
                "user_id": context.user_id
            }

            return final_recommendations

        except Exception as e:
            logger.error(f"❌ 추천 종합 실패: {e}")
            return await self._get_fallback_recommendations(context.user_id)

    async def _get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """사용자 프로필 조회"""
        try:
            query = """
                SELECT user_id, preferences, demographics,
                       purchase_history, created_at, updated_at
                FROM users
                WHERE user_id = $1
            """

            async with self.db_manager.get_connection() as conn:
                row = await conn.fetchrow(query, user_id)

                if row:
                    return {
                        "user_id": row['user_id'],
                        "preferences": json.loads(row['preferences'] or '{}'),
                        "demographics": json.loads(row['demographics'] or '{}'),
                        "purchase_history": json.loads(row['purchase_history'] or '[]'),
                        "account_age_days": (datetime.now() - row['created_at']).days
                    }
                else:
                    return {"user_id": user_id, "preferences": {}, "demographics": {}, "purchase_history": []}

        except Exception as e:
            logger.error(f"❌ 사용자 프로필 조회 실패: {e}")
            return {"user_id": user_id, "preferences": {}, "demographics": {}, "purchase_history": []}

    async def _get_interaction_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """상호작용 히스토리 조회"""
        try:
            query = """
                SELECT user_id, vehicle_id, interaction_type, timestamp,
                       context_data, engagement_score
                FROM user_interactions
                WHERE user_id = $1
                ORDER BY timestamp DESC
                LIMIT $2
            """

            async with self.db_manager.get_connection() as conn:
                rows = await conn.fetch(query, user_id, limit)

                return [
                    {
                        "vehicle_id": row['vehicle_id'],
                        "interaction_type": row['interaction_type'],
                        "timestamp": row['timestamp'].isoformat(),
                        "context": json.loads(row['context_data'] or '{}'),
                        "engagement_score": row['engagement_score']
                    }
                    for row in rows
                ]

        except Exception as e:
            logger.error(f"❌ 상호작용 히스토리 조회 실패: {e}")
            return []

    async def _get_market_context(self) -> Dict[str, Any]:
        """시장 컨텍스트 조회"""
        try:
            # 인기 차량 조회
            popular_query = """
                SELECT vehicle_id, COUNT(*) as interaction_count
                FROM user_interactions
                WHERE timestamp > NOW() - INTERVAL '7 days'
                GROUP BY vehicle_id
                ORDER BY interaction_count DESC
                LIMIT 10
            """

            # 가격 트렌드 조회 (최근 30일)
            price_query = """
                SELECT AVG(price) as avg_price, vehicle_type
                FROM vehicles v
                JOIN user_interactions ui ON v.vehicle_id = ui.vehicle_id
                WHERE ui.timestamp > NOW() - INTERVAL '30 days'
                GROUP BY vehicle_type
            """

            async with self.db_manager.get_connection() as conn:
                popular_vehicles = await conn.fetch(popular_query)
                price_trends = await conn.fetch(price_query)

                return {
                    "popular_vehicles": [
                        {"vehicle_id": row['vehicle_id'], "popularity": row['interaction_count']}
                        for row in popular_vehicles
                    ],
                    "price_trends": [
                        {"vehicle_type": row['vehicle_type'], "avg_price": float(row['avg_price'])}
                        for row in price_trends
                    ],
                    "market_timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"❌ 시장 컨텍스트 조회 실패: {e}")
            return {"popular_vehicles": [], "price_trends": [], "market_timestamp": datetime.now().isoformat()}

    async def _get_fallback_recommendations(self, user_id: str) -> Dict[str, Any]:
        """실패 시 기본 추천"""
        try:
            # 기본적인 인기 차량 추천
            query = """
                SELECT v.vehicle_id, v.make, v.model, v.price, COUNT(ui.interaction_id) as popularity
                FROM vehicles v
                LEFT JOIN user_interactions ui ON v.vehicle_id = ui.vehicle_id
                WHERE ui.timestamp > NOW() - INTERVAL '7 days' OR ui.timestamp IS NULL
                GROUP BY v.vehicle_id, v.make, v.model, v.price
                ORDER BY popularity DESC, v.price ASC
                LIMIT 5
            """

            async with self.db_manager.get_connection() as conn:
                rows = await conn.fetch(query)

                recommendations = [
                    {
                        "vehicle_id": row['vehicle_id'],
                        "make": row['make'],
                        "model": row['model'],
                        "price": float(row['price']),
                        "confidence_score": 0.3,
                        "reasoning": "기본 인기 차량 추천"
                    }
                    for row in rows
                ]

                return {
                    "recommendations": recommendations,
                    "confidence_score": 0.3,
                    "reasoning": "멀티에이전트 시스템 실패로 인한 기본 추천",
                    "agent_contributions": {},
                    "timestamp": datetime.now().isoformat(),
                    "user_id": user_id,
                    "fallback": True
                }

        except Exception as e:
            logger.error(f"❌ 기본 추천 생성 실패: {e}")
            return {
                "recommendations": [],
                "confidence_score": 0.1,
                "reasoning": "시스템 오류로 인한 빈 추천",
                "agent_contributions": {},
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "error": True
            }

# 싱글톤 인스턴스
_multi_agent_system = None

async def get_gemini_multi_agent_system(api_key: str = None) -> GeminiMultiAgentSystem:
    """Gemini 멀티에이전트 시스템 인스턴스 조회"""
    global _multi_agent_system

    if _multi_agent_system is None:
        if not api_key:
            raise ValueError("Gemini API 키가 필요합니다")
        _multi_agent_system = GeminiMultiAgentSystem(api_key)

    return _multi_agent_system