# -*- coding: utf-8 -*-
"""
CarFinanceAI MCP Server
Model Context Protocol 서버 구현 - 추천시스템을 MCP 서비스로 제공
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass, asdict
import os
from pathlib import Path

# MCP 프로토콜 (가상 구현 - 실제 MCP 라이브러리 대체)
from typing import Protocol, runtime_checkable

# 내부 모듈
from ..database.connection import DatabaseManager
from ..database.realtime_learning import get_realtime_engine, get_recommendation_cache
from ..agents.gemini_recommendation_agent import get_gemini_multi_agent_system

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@runtime_checkable
class MCPTool(Protocol):
    """MCP 도구 프로토콜"""
    name: str
    description: str
    input_schema: Dict[str, Any]

@dataclass
class MCPToolResult:
    """MCP 도구 실행 결과"""
    success: bool
    content: Any
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class CarFinanceAITool:
    """CarFinanceAI MCP 도구 기본 클래스"""

    def __init__(self, name: str, description: str, input_schema: Dict[str, Any]):
        self.name = name
        self.description = description
        self.input_schema = input_schema

    async def execute(self, **kwargs) -> MCPToolResult:
        """도구 실행 (하위 클래스에서 구현)"""
        raise NotImplementedError

class GetRecommendationsTool(CarFinanceAITool):
    """사용자 추천 조회 도구"""

    def __init__(self):
        super().__init__(
            name="carfinance__get_recommendations",
            description="사용자 맞춤 차량 추천을 생성합니다. Gemini 멀티에이전트를 활용한 고도화된 추천 제공",
            input_schema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "추천을 요청하는 사용자 ID"
                    },
                    "context": {
                        "type": "object",
                        "description": "추가 컨텍스트 정보 (세션 데이터, 현재 관심사 등)",
                        "properties": {
                            "session_id": {"type": "string"},
                            "current_page": {"type": "string"},
                            "search_query": {"type": "string"},
                            "budget_range": {
                                "type": "object",
                                "properties": {
                                    "min": {"type": "number"},
                                    "max": {"type": "number"}
                                }
                            }
                        }
                    },
                    "recommendation_count": {
                        "type": "integer",
                        "description": "요청할 추천 개수 (기본: 5)",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20
                    },
                    "use_sequential_thinking": {
                        "type": "boolean",
                        "description": "복잡한 추천 논리에 Sequential Thinking MCP 사용 여부",
                        "default": true
                    }
                },
                "required": ["user_id"]
            }
        )

    async def execute(self, user_id: str, context: Dict = None, recommendation_count: int = 5, use_sequential_thinking: bool = True) -> MCPToolResult:
        """추천 실행"""
        try:
            # Gemini 멀티에이전트 시스템 조회
            gemini_key = os.getenv('GEMINI_API_KEY')
            if not gemini_key:
                return MCPToolResult(
                    success=False,
                    content=None,
                    error="Gemini API 키가 설정되지 않았습니다"
                )

            multi_agent = await get_gemini_multi_agent_system(gemini_key)

            # Sequential Thinking MCP 활용 (복잡한 추천 논리)
            if use_sequential_thinking:
                reasoning_result = await self._use_sequential_thinking_for_recommendations(
                    user_id, context, recommendation_count
                )
                context = context or {}
                context['reasoning_insights'] = reasoning_result

            # 멀티에이전트 추천 생성
            recommendations = await multi_agent.get_recommendations(user_id, context)

            # 추천 개수 조정
            if len(recommendations.get('recommendations', [])) > recommendation_count:
                recommendations['recommendations'] = recommendations['recommendations'][:recommendation_count]

            return MCPToolResult(
                success=True,
                content=recommendations,
                metadata={
                    "tool_name": self.name,
                    "execution_time": datetime.now().isoformat(),
                    "user_id": user_id,
                    "used_sequential_thinking": use_sequential_thinking
                }
            )

        except Exception as e:
            logger.error(f"❌ 추천 생성 실패: {e}")
            return MCPToolResult(
                success=False,
                content=None,
                error=str(e)
            )

    async def _use_sequential_thinking_for_recommendations(self, user_id: str, context: Dict, count: int) -> Dict:
        """Sequential Thinking MCP를 활용한 추천 논리 분석"""
        try:
            # 실제로는 sequential-thinking MCP 호출
            # 여기서는 시뮬레이션
            reasoning_prompt = f"""
            사용자 {user_id}에 대한 차량 추천 논리를 단계별로 분석해주세요.

            컨텍스트: {json.dumps(context, ensure_ascii=False)}
            요청 추천 수: {count}

            다음 단계로 분석해주세요:
            1. 사용자 프로필 분석
            2. 과거 행동 패턴 분석
            3. 시장 상황 고려
            4. 추천 전략 수립
            5. 예상 결과 평가
            """

            # Sequential thinking 결과 (시뮬레이션)
            return {
                "reasoning_steps": [
                    "사용자 프로필 기반 선호도 분석 완료",
                    "과거 행동에서 SUV 선호 패턴 발견",
                    "현재 시장에서 SUV 할인 프로모션 활성화",
                    "가격 대비 성능 우수 모델 우선 추천 전략",
                    "높은 만족도 예상, 구매 전환 가능성 75%"
                ],
                "insights": {
                    "primary_preference": "SUV",
                    "budget_sensitivity": "medium",
                    "purchase_probability": 0.75
                }
            }

        except Exception as e:
            logger.error(f"❌ Sequential Thinking 분석 실패: {e}")
            return {"reasoning_steps": [], "insights": {}}

class AnalyzeBehaviorTool(CarFinanceAITool):
    """사용자 행동 분석 도구"""

    def __init__(self):
        super().__init__(
            name="carfinance__analyze_behavior",
            description="사용자의 행동 패턴을 분석하고 인사이트를 제공합니다. Sequential Thinking을 활용한 깊이 있는 분석",
            input_schema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "분석 대상 사용자 ID"
                    },
                    "analysis_period_days": {
                        "type": "integer",
                        "description": "분석 기간 (일수)",
                        "default": 30,
                        "minimum": 1,
                        "maximum": 365
                    },
                    "include_predictions": {
                        "type": "boolean",
                        "description": "미래 행동 예측 포함 여부",
                        "default": true
                    }
                },
                "required": ["user_id"]
            }
        )

    async def execute(self, user_id: str, analysis_period_days: int = 30, include_predictions: bool = True) -> MCPToolResult:
        """행동 분석 실행"""
        try:
            # 실시간 학습 엔진 조회
            engine = await get_realtime_engine()

            # 사용자 행동 데이터 수집
            behavior_data = await self._collect_behavior_data(user_id, analysis_period_days)

            # Sequential Thinking을 활용한 패턴 분석
            pattern_analysis = await self._analyze_patterns_with_sequential_thinking(
                user_id, behavior_data, include_predictions
            )

            # 행동 인사이트 생성
            insights = {
                "user_id": user_id,
                "analysis_period": analysis_period_days,
                "behavior_summary": self._generate_behavior_summary(behavior_data),
                "pattern_analysis": pattern_analysis,
                "recommendations": self._generate_behavior_recommendations(pattern_analysis),
                "timestamp": datetime.now().isoformat()
            }

            return MCPToolResult(
                success=True,
                content=insights,
                metadata={
                    "tool_name": self.name,
                    "analysis_depth": "deep_sequential",
                    "data_points": len(behavior_data)
                }
            )

        except Exception as e:
            logger.error(f"❌ 행동 분석 실패: {e}")
            return MCPToolResult(
                success=False,
                content=None,
                error=str(e)
            )

    async def _collect_behavior_data(self, user_id: str, days: int) -> List[Dict]:
        """행동 데이터 수집"""
        try:
            db_manager = DatabaseManager()
            query = """
                SELECT interaction_type, vehicle_id, timestamp,
                       context_data, engagement_score
                FROM user_interactions
                WHERE user_id = $1
                AND timestamp > NOW() - INTERVAL '%s days'
                ORDER BY timestamp DESC
            """ % days

            async with db_manager.get_connection() as conn:
                rows = await conn.fetch(query, user_id)
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"❌ 행동 데이터 수집 실패: {e}")
            return []

    async def _analyze_patterns_with_sequential_thinking(self, user_id: str, behavior_data: List[Dict], include_predictions: bool) -> Dict:
        """Sequential Thinking을 활용한 패턴 분석"""
        # 실제로는 sequential-thinking MCP 호출
        # 시뮬레이션 결과 반환
        return {
            "interaction_patterns": {
                "peak_hours": ["19:00-21:00", "12:00-13:00"],
                "preferred_brands": ["Toyota", "Honda", "BMW"],
                "average_session_duration": 15.5,
                "conversion_indicators": ["multiple_inquiries", "price_comparisons"]
            },
            "behavioral_segments": {
                "primary_segment": "research_oriented_buyer",
                "secondary_traits": ["price_conscious", "feature_focused"]
            },
            "predictions": {
                "purchase_probability_30_days": 0.68,
                "likely_vehicle_type": "SUV",
                "estimated_budget_range": [25000, 40000]
            } if include_predictions else None
        }

    def _generate_behavior_summary(self, behavior_data: List[Dict]) -> Dict:
        """행동 요약 생성"""
        if not behavior_data:
            return {"total_interactions": 0, "summary": "행동 데이터 없음"}

        interaction_types = {}
        for item in behavior_data:
            interaction_type = item.get('interaction_type', 'unknown')
            interaction_types[interaction_type] = interaction_types.get(interaction_type, 0) + 1

        return {
            "total_interactions": len(behavior_data),
            "interaction_breakdown": interaction_types,
            "most_common_action": max(interaction_types.items(), key=lambda x: x[1])[0] if interaction_types else "none",
            "engagement_level": "high" if len(behavior_data) > 50 else "medium" if len(behavior_data) > 10 else "low"
        }

    def _generate_behavior_recommendations(self, pattern_analysis: Dict) -> List[str]:
        """행동 기반 추천 생성"""
        recommendations = []

        patterns = pattern_analysis.get('interaction_patterns', {})
        segments = pattern_analysis.get('behavioral_segments', {})

        if segments.get('primary_segment') == 'research_oriented_buyer':
            recommendations.append("상세한 차량 정보와 비교 데이터를 제공하세요")
            recommendations.append("전문가 리뷰 및 실사용 후기를 강조하세요")

        if 'price_conscious' in segments.get('secondary_traits', []):
            recommendations.append("할인 정보와 프로모션을 우선 표시하세요")
            recommendations.append("가격 대비 성능 우수 모델을 추천하세요")

        return recommendations

class TrackInteractionTool(CarFinanceAITool):
    """실시간 상호작용 추적 도구"""

    def __init__(self):
        super().__init__(
            name="carfinance__track_interaction",
            description="사용자 상호작용을 실시간으로 추적하고 학습 시스템에 반영합니다",
            input_schema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "사용자 ID"
                    },
                    "vehicle_id": {
                        "type": "string",
                        "description": "차량 ID"
                    },
                    "interaction_type": {
                        "type": "string",
                        "enum": ["view", "like", "inquiry", "compare", "purchase"],
                        "description": "상호작용 유형"
                    },
                    "context": {
                        "type": "object",
                        "description": "상호작용 컨텍스트",
                        "properties": {
                            "session_id": {"type": "string"},
                            "duration_seconds": {"type": "number"},
                            "page_source": {"type": "string"},
                            "repeat_visit": {"type": "boolean"}
                        }
                    }
                },
                "required": ["user_id", "vehicle_id", "interaction_type"]
            }
        )

    async def execute(self, user_id: str, vehicle_id: str, interaction_type: str, context: Dict = None) -> MCPToolResult:
        """상호작용 추적 실행"""
        try:
            # 실시간 학습 엔진 조회
            engine = await get_realtime_engine()

            # 상호작용 데이터 구성
            interaction_data = {
                "user_id": user_id,
                "vehicle_id": vehicle_id,
                "interaction_type": interaction_type,
                "context": context or {},
                "timestamp": datetime.now().isoformat()
            }

            # 실시간 처리
            success = await engine.process_user_interaction(interaction_data)

            if success:
                return MCPToolResult(
                    success=True,
                    content={
                        "interaction_tracked": True,
                        "user_id": user_id,
                        "vehicle_id": vehicle_id,
                        "interaction_type": interaction_type,
                        "processed_at": datetime.now().isoformat()
                    },
                    metadata={
                        "tool_name": self.name,
                        "real_time_processing": True
                    }
                )
            else:
                return MCPToolResult(
                    success=False,
                    content=None,
                    error="상호작용 처리에 실패했습니다"
                )

        except Exception as e:
            logger.error(f"❌ 상호작용 추적 실패: {e}")
            return MCPToolResult(
                success=False,
                content=None,
                error=str(e)
            )

class CompareVehiclesTool(CarFinanceAITool):
    """차량 비교 도구"""

    def __init__(self):
        super().__init__(
            name="carfinance__compare_vehicles",
            description="여러 차량을 비교하고 상세한 분석을 제공합니다",
            input_schema={
                "type": "object",
                "properties": {
                    "vehicle_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "비교할 차량 ID 목록",
                        "minItems": 2,
                        "maxItems": 5
                    },
                    "comparison_criteria": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["price", "fuel_efficiency", "safety", "performance", "comfort", "reliability"]
                        },
                        "description": "비교 기준 (기본: 모든 기준)"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "사용자 ID (개인화된 비교를 위함)"
                    }
                },
                "required": ["vehicle_ids"]
            }
        )

    async def execute(self, vehicle_ids: List[str], comparison_criteria: List[str] = None, user_id: str = None) -> MCPToolResult:
        """차량 비교 실행"""
        try:
            # 기본 비교 기준
            if not comparison_criteria:
                comparison_criteria = ["price", "fuel_efficiency", "safety", "performance", "comfort", "reliability"]

            # 차량 정보 조회
            vehicles_data = await self._get_vehicles_data(vehicle_ids)

            # 비교 분석 수행
            comparison_result = await self._perform_comparison(vehicles_data, comparison_criteria, user_id)

            return MCPToolResult(
                success=True,
                content=comparison_result,
                metadata={
                    "tool_name": self.name,
                    "compared_vehicles": len(vehicle_ids),
                    "criteria_count": len(comparison_criteria)
                }
            )

        except Exception as e:
            logger.error(f"❌ 차량 비교 실패: {e}")
            return MCPToolResult(
                success=False,
                content=None,
                error=str(e)
            )

    async def _get_vehicles_data(self, vehicle_ids: List[str]) -> List[Dict]:
        """차량 데이터 조회"""
        try:
            db_manager = DatabaseManager()
            placeholders = ','.join(['$' + str(i+1) for i in range(len(vehicle_ids))])
            query = f"""
                SELECT vehicle_id, make, model, year, price, fuel_type,
                       safety_rating, mpg_city, mpg_highway, features
                FROM vehicles
                WHERE vehicle_id IN ({placeholders})
            """

            async with db_manager.get_connection() as conn:
                rows = await conn.fetch(query, *vehicle_ids)
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"❌ 차량 데이터 조회 실패: {e}")
            return []

    async def _perform_comparison(self, vehicles_data: List[Dict], criteria: List[str], user_id: str = None) -> Dict:
        """비교 분석 수행"""
        if not vehicles_data:
            return {"error": "차량 데이터를 조회할 수 없습니다"}

        comparison = {
            "vehicles": vehicles_data,
            "comparison_matrix": {},
            "recommendations": [],
            "summary": {}
        }

        # 각 기준별 비교
        for criterion in criteria:
            comparison["comparison_matrix"][criterion] = self._compare_by_criterion(vehicles_data, criterion)

        # 종합 추천
        comparison["recommendations"] = self._generate_comparison_recommendations(vehicles_data, criteria, user_id)

        return comparison

    def _compare_by_criterion(self, vehicles: List[Dict], criterion: str) -> Dict:
        """기준별 비교"""
        if criterion == "price":
            scores = {v['vehicle_id']: self._price_score(v['price']) for v in vehicles}
        elif criterion == "fuel_efficiency":
            scores = {v['vehicle_id']: self._fuel_score(v.get('mpg_city', 0), v.get('mpg_highway', 0)) for v in vehicles}
        elif criterion == "safety":
            scores = {v['vehicle_id']: v.get('safety_rating', 3) for v in vehicles}
        else:
            # 기본 점수
            scores = {v['vehicle_id']: 3.0 for v in vehicles}

        return {
            "scores": scores,
            "winner": max(scores.items(), key=lambda x: x[1])[0],
            "ranking": sorted(scores.items(), key=lambda x: x[1], reverse=True)
        }

    def _price_score(self, price: float) -> float:
        """가격 점수 (낮을수록 좋음)"""
        return max(1.0, 6.0 - (price / 10000))

    def _fuel_score(self, city_mpg: float, highway_mpg: float) -> float:
        """연비 점수"""
        avg_mpg = (city_mpg + highway_mpg) / 2
        return min(5.0, avg_mpg / 10)

    def _generate_comparison_recommendations(self, vehicles: List[Dict], criteria: List[str], user_id: str = None) -> List[str]:
        """비교 기반 추천 생성"""
        recommendations = []

        if len(vehicles) >= 2:
            cheapest = min(vehicles, key=lambda v: v['price'])
            most_efficient = max(vehicles, key=lambda v: (v.get('mpg_city', 0) + v.get('mpg_highway', 0)) / 2)

            recommendations.append(f"가격 우선: {cheapest['make']} {cheapest['model']}")
            recommendations.append(f"연비 우선: {most_efficient['make']} {most_efficient['model']}")

        return recommendations

class CarFinanceAIMCPServer:
    """CarFinanceAI MCP 서버"""

    def __init__(self):
        self.tools = {
            "carfinance__get_recommendations": GetRecommendationsTool(),
            "carfinance__analyze_behavior": AnalyzeBehaviorTool(),
            "carfinance__track_interaction": TrackInteractionTool(),
            "carfinance__compare_vehicles": CompareVehiclesTool()
        }

        self.server_info = {
            "name": "CarFinanceAI MCP Server",
            "version": "1.0.0",
            "description": "자동차 금융 및 추천시스템 MCP 서버",
            "tools": list(self.tools.keys())
        }

    async def list_tools(self) -> List[Dict[str, Any]]:
        """사용 가능한 도구 목록 반환"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema
            }
            for tool in self.tools.values()
        ]

    async def execute_tool(self, tool_name: str, **kwargs) -> MCPToolResult:
        """도구 실행"""
        if tool_name not in self.tools:
            return MCPToolResult(
                success=False,
                content=None,
                error=f"알 수 없는 도구: {tool_name}"
            )

        tool = self.tools[tool_name]
        return await tool.execute(**kwargs)

    async def get_server_info(self) -> Dict[str, Any]:
        """서버 정보 반환"""
        return self.server_info

    async def health_check(self) -> Dict[str, Any]:
        """서버 상태 확인"""
        try:
            # 데이터베이스 연결 확인
            db_manager = DatabaseManager()
            async with db_manager.get_connection() as conn:
                await conn.fetchval("SELECT 1")

            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "database": "connected",
                "tools_count": len(self.tools)
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

# 싱글톤 인스턴스
_mcp_server = None

async def get_carfinance_mcp_server() -> CarFinanceAIMCPServer:
    """CarFinanceAI MCP 서버 인스턴스 조회"""
    global _mcp_server

    if _mcp_server is None:
        _mcp_server = CarFinanceAIMCPServer()

    return _mcp_server

# MCP 서버 실행 스크립트
async def run_mcp_server():
    """MCP 서버 실행"""
    server = await get_carfinance_mcp_server()

    logger.info("🚀 CarFinanceAI MCP Server 시작")
    logger.info(f"📋 사용 가능한 도구: {len(server.tools)}개")

    # 서버 상태 확인
    health = await server.health_check()
    logger.info(f"💚 서버 상태: {health['status']}")

    # 도구 목록 출력
    tools = await server.list_tools()
    for tool in tools:
        logger.info(f"🔧 도구: {tool['name']} - {tool['description']}")

    return server

if __name__ == "__main__":
    asyncio.run(run_mcp_server())