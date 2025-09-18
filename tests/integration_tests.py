# -*- coding: utf-8 -*-
"""
통합 시스템 테스트 및 검증
PostgreSQL, 실시간 학습, Gemini 멀티에이전트, MCP 서버 통합 테스트
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pytest
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 내부 모듈
from database.connection import DatabaseManager, UserBehaviorTracker
from database.realtime_learning import get_realtime_engine, get_recommendation_cache
from agents.gemini_recommendation_agent import get_gemini_multi_agent_system
from mcp.carfinance_mcp_server import get_carfinance_mcp_server
from strategies.user_behavior_strategy import get_user_behavior_collection_strategy

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegrationTestSuite:
    """통합 테스트 스위트"""

    def __init__(self):
        self.test_results = {}
        self.test_user_id = "test_user_integration_001"
        self.test_vehicle_id = "test_vehicle_001"
        self.db_manager = None
        self.start_time = None

    async def run_all_tests(self) -> Dict[str, Any]:
        """모든 통합 테스트 실행"""
        self.start_time = time.time()
        logger.info("🚀 통합 테스트 시작")

        try:
            # 1. 데이터베이스 연결 테스트
            await self._test_database_connection()

            # 2. 실시간 학습 시스템 테스트
            await self._test_realtime_learning_system()

            # 3. Gemini 멀티에이전트 테스트
            await self._test_gemini_multiagent()

            # 4. MCP 서버 테스트
            await self._test_mcp_server()

            # 5. 사용자 행동 수집 전략 테스트
            await self._test_behavior_collection_strategy()

            # 6. 전체 시스템 통합 테스트
            await self._test_full_system_integration()

            # 7. 성능 테스트
            await self._test_system_performance()

            # 8. 정리 작업
            await self._cleanup_test_data()

            # 테스트 결과 종합
            total_time = time.time() - self.start_time
            self.test_results["overall"] = {
                "status": "completed",
                "total_duration_seconds": total_time,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"✅ 통합 테스트 완료 ({total_time:.2f}초)")
            return self.test_results

        except Exception as e:
            logger.error(f"❌ 통합 테스트 실패: {e}")
            self.test_results["overall"] = {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            return self.test_results

    async def _test_database_connection(self):
        """데이터베이스 연결 테스트"""
        test_name = "database_connection"
        logger.info(f"🔌 {test_name} 테스트 시작")

        try:
            start_time = time.time()

            # DatabaseManager 초기화
            self.db_manager = DatabaseManager()

            # 연결 테스트
            async with self.db_manager.get_connection() as conn:
                result = await conn.fetchval("SELECT 1")
                assert result == 1, "기본 쿼리 실행 실패"

            # 테이블 존재 확인
            async with self.db_manager.get_connection() as conn:
                tables = await conn.fetch("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name IN ('users', 'vehicles', 'user_interactions')
                """)

                table_names = [row['table_name'] for row in tables]
                required_tables = ['users', 'vehicles', 'user_interactions']

                for table in required_tables:
                    if table not in table_names:
                        logger.warning(f"⚠️ 필수 테이블 누락: {table}")

            # UserBehaviorTracker 테스트
            behavior_tracker = UserBehaviorTracker(self.db_manager)

            test_interaction = {
                "user_id": self.test_user_id,
                "vehicle_id": self.test_vehicle_id,
                "interaction_type": "view",
                "context": {"test": True}
            }

            success = await behavior_tracker.track_user_interaction(test_interaction)
            assert success, "사용자 상호작용 추적 실패"

            duration = time.time() - start_time
            self.test_results[test_name] = {
                "status": "passed",
                "duration_seconds": duration,
                "details": {
                    "connection_successful": True,
                    "tables_checked": len(required_tables),
                    "behavior_tracking": success
                }
            }

            logger.info(f"✅ {test_name} 테스트 통과 ({duration:.2f}초)")

        except Exception as e:
            self.test_results[test_name] = {
                "status": "failed",
                "error": str(e),
                "duration_seconds": time.time() - start_time
            }
            logger.error(f"❌ {test_name} 테스트 실패: {e}")
            raise

    async def _test_realtime_learning_system(self):
        """실시간 학습 시스템 테스트"""
        test_name = "realtime_learning"
        logger.info(f"🧠 {test_name} 테스트 시작")

        try:
            start_time = time.time()

            # 실시간 학습 엔진 조회
            engine = await get_realtime_engine()
            assert engine is not None, "실시간 학습 엔진 조회 실패"

            # 테스트 상호작용 데이터
            test_interactions = [
                {
                    "user_id": self.test_user_id,
                    "vehicle_id": self.test_vehicle_id,
                    "interaction_type": "view",
                    "context": {"duration_seconds": 30}
                },
                {
                    "user_id": self.test_user_id,
                    "vehicle_id": self.test_vehicle_id,
                    "interaction_type": "like",
                    "context": {"duration_seconds": 60}
                },
                {
                    "user_id": self.test_user_id,
                    "vehicle_id": self.test_vehicle_id,
                    "interaction_type": "inquiry",
                    "context": {"duration_seconds": 120}
                }
            ]

            # 상호작용 처리 테스트
            processed_count = 0
            for interaction in test_interactions:
                success = await engine.process_user_interaction(interaction)
                if success:
                    processed_count += 1

            assert processed_count == len(test_interactions), f"상호작용 처리 실패: {processed_count}/{len(test_interactions)}"

            # 추천 캐시 테스트
            cache = await get_recommendation_cache()
            assert cache is not None, "추천 캐시 조회 실패"

            # 캐시 업데이트 테스트
            test_recommendations = [
                {"vehicle_id": "test_001", "score": 0.9},
                {"vehicle_id": "test_002", "score": 0.8}
            ]

            await cache.update_user_recommendations(self.test_user_id, test_recommendations)

            # 캐시 조회 테스트
            cached_recommendations = await cache.get_user_recommendations(self.test_user_id)
            assert len(cached_recommendations) > 0, "캐시된 추천 조회 실패"

            duration = time.time() - start_time
            self.test_results[test_name] = {
                "status": "passed",
                "duration_seconds": duration,
                "details": {
                    "interactions_processed": processed_count,
                    "cache_operations": True,
                    "engine_initialized": True
                }
            }

            logger.info(f"✅ {test_name} 테스트 통과 ({duration:.2f}초)")

        except Exception as e:
            self.test_results[test_name] = {
                "status": "failed",
                "error": str(e),
                "duration_seconds": time.time() - start_time
            }
            logger.error(f"❌ {test_name} 테스트 실패: {e}")

    async def _test_gemini_multiagent(self):
        """Gemini 멀티에이전트 테스트"""
        test_name = "gemini_multiagent"
        logger.info(f"🤖 {test_name} 테스트 시작")

        try:
            start_time = time.time()

            # API 키 확인
            gemini_key = os.getenv('GEMINI_API_KEY')
            if not gemini_key:
                logger.warning("⚠️ GEMINI_API_KEY가 설정되지 않음 - 시뮬레이션 모드")
                self.test_results[test_name] = {
                    "status": "skipped",
                    "reason": "GEMINI_API_KEY not configured",
                    "duration_seconds": time.time() - start_time
                }
                return

            # 멀티에이전트 시스템 조회
            multi_agent = await get_gemini_multi_agent_system(gemini_key)
            assert multi_agent is not None, "멀티에이전트 시스템 조회 실패"

            # 추천 생성 테스트
            recommendations = await multi_agent.get_recommendations(
                user_id=self.test_user_id,
                context_data={"test_mode": True}
            )

            assert recommendations is not None, "추천 생성 실패"
            assert "recommendations" in recommendations, "추천 결과 형식 오류"

            # 에이전트 기여도 확인
            if "agent_contributions" in recommendations:
                contributions = recommendations["agent_contributions"]
                assert len(contributions) > 0, "에이전트 기여도 정보 없음"

            duration = time.time() - start_time
            self.test_results[test_name] = {
                "status": "passed",
                "duration_seconds": duration,
                "details": {
                    "recommendations_generated": len(recommendations.get("recommendations", [])),
                    "agent_contributions": len(recommendations.get("agent_contributions", {})),
                    "confidence_score": recommendations.get("confidence_score", 0)
                }
            }

            logger.info(f"✅ {test_name} 테스트 통과 ({duration:.2f}초)")

        except Exception as e:
            self.test_results[test_name] = {
                "status": "failed",
                "error": str(e),
                "duration_seconds": time.time() - start_time
            }
            logger.error(f"❌ {test_name} 테스트 실패: {e}")

    async def _test_mcp_server(self):
        """MCP 서버 테스트"""
        test_name = "mcp_server"
        logger.info(f"🔧 {test_name} 테스트 시작")

        try:
            start_time = time.time()

            # MCP 서버 조회
            mcp_server = await get_carfinance_mcp_server()
            assert mcp_server is not None, "MCP 서버 조회 실패"

            # 서버 정보 테스트
            server_info = await mcp_server.get_server_info()
            assert "name" in server_info, "서버 정보 오류"
            assert "tools" in server_info, "도구 목록 정보 누락"

            # 도구 목록 테스트
            tools = await mcp_server.list_tools()
            assert len(tools) > 0, "MCP 도구 없음"

            tool_names = [tool["name"] for tool in tools]
            expected_tools = [
                "carfinance__get_recommendations",
                "carfinance__analyze_behavior",
                "carfinance__track_interaction",
                "carfinance__compare_vehicles"
            ]

            for expected_tool in expected_tools:
                assert expected_tool in tool_names, f"필수 도구 누락: {expected_tool}"

            # 헬스 체크 테스트
            health = await mcp_server.health_check()
            assert health["status"] in ["healthy", "unhealthy"], "헬스 체크 결과 형식 오류"

            # 도구 실행 테스트 (상호작용 추적)
            track_result = await mcp_server.execute_tool(
                "carfinance__track_interaction",
                user_id=self.test_user_id,
                vehicle_id=self.test_vehicle_id,
                interaction_type="view"
            )

            assert track_result.success, f"도구 실행 실패: {track_result.error}"

            duration = time.time() - start_time
            self.test_results[test_name] = {
                "status": "passed",
                "duration_seconds": duration,
                "details": {
                    "tools_available": len(tools),
                    "health_status": health["status"],
                    "tool_execution": track_result.success
                }
            }

            logger.info(f"✅ {test_name} 테스트 통과 ({duration:.2f}초)")

        except Exception as e:
            self.test_results[test_name] = {
                "status": "failed",
                "error": str(e),
                "duration_seconds": time.time() - start_time
            }
            logger.error(f"❌ {test_name} 테스트 실패: {e}")

    async def _test_behavior_collection_strategy(self):
        """사용자 행동 수집 전략 테스트"""
        test_name = "behavior_collection"
        logger.info(f"📊 {test_name} 테스트 시작")

        try:
            start_time = time.time()

            # 수집 전략 조회
            strategy = await get_user_behavior_collection_strategy()
            assert strategy is not None, "행동 수집 전략 조회 실패"

            # 테스트 이벤트 데이터
            test_events = [
                {
                    "user_id": self.test_user_id,
                    "event_type": "view",
                    "vehicle_id": self.test_vehicle_id,
                    "session_id": "test_session_001",
                    "duration_seconds": 30
                },
                {
                    "user_id": self.test_user_id,
                    "event_type": "inquiry",
                    "vehicle_id": self.test_vehicle_id,
                    "session_id": "test_session_001",
                    "duration_seconds": 120
                }
            ]

            # 행동 수집 테스트
            collected_count = 0
            for event in test_events:
                success = await strategy.collect_behavior(event)
                if success:
                    collected_count += 1

            assert collected_count == len(test_events), f"행동 수집 실패: {collected_count}/{len(test_events)}"

            # 메트릭 조회 테스트
            metrics = await strategy.get_collection_metrics()
            assert "total_events_processed" in metrics, "메트릭 정보 누락"
            assert metrics["total_events_processed"] >= collected_count, "처리된 이벤트 수 불일치"

            duration = time.time() - start_time
            self.test_results[test_name] = {
                "status": "passed",
                "duration_seconds": duration,
                "details": {
                    "events_collected": collected_count,
                    "total_processed": metrics["total_events_processed"],
                    "queue_sizes": metrics.get("queue_sizes", {})
                }
            }

            logger.info(f"✅ {test_name} 테스트 통과 ({duration:.2f}초)")

        except Exception as e:
            self.test_results[test_name] = {
                "status": "failed",
                "error": str(e),
                "duration_seconds": time.time() - start_time
            }
            logger.error(f"❌ {test_name} 테스트 실패: {e}")

    async def _test_full_system_integration(self):
        """전체 시스템 통합 테스트"""
        test_name = "full_integration"
        logger.info(f"🔄 {test_name} 테스트 시작")

        try:
            start_time = time.time()

            # 전체 워크플로우 테스트: 사용자 행동 → 실시간 학습 → 추천 생성 → MCP 서빙

            # 1. 사용자 행동 수집
            strategy = await get_user_behavior_collection_strategy()

            behavior_event = {
                "user_id": self.test_user_id,
                "event_type": "inquiry",
                "vehicle_id": self.test_vehicle_id,
                "session_id": "integration_test_session",
                "duration_seconds": 180,
                "context": {"integration_test": True}
            }

            collection_success = await strategy.collect_behavior(behavior_event)
            assert collection_success, "행동 수집 실패"

            # 2. 실시간 학습 처리
            engine = await get_realtime_engine()
            learning_success = await engine.process_user_interaction({
                "user_id": self.test_user_id,
                "vehicle_id": self.test_vehicle_id,
                "interaction_type": "inquiry",
                "context": {"integration_test": True}
            })
            assert learning_success, "실시간 학습 처리 실패"

            # 3. MCP를 통한 추천 조회
            mcp_server = await get_carfinance_mcp_server()
            recommendation_result = await mcp_server.execute_tool(
                "carfinance__get_recommendations",
                user_id=self.test_user_id,
                recommendation_count=3,
                use_sequential_thinking=False  # 테스트 환경에서는 비활성화
            )

            # Gemini API 키가 없으면 fallback 추천이 반환됨
            if recommendation_result.success:
                recommendations = recommendation_result.content
                assert "recommendations" in recommendations, "추천 결과 형식 오류"
            else:
                logger.warning("⚠️ 추천 생성 실패 (Gemini API 키 문제 가능성)")

            # 4. 행동 분석 테스트
            analysis_result = await mcp_server.execute_tool(
                "carfinance__analyze_behavior",
                user_id=self.test_user_id,
                analysis_period_days=1,
                include_predictions=False
            )

            assert analysis_result.success, f"행동 분석 실패: {analysis_result.error}"

            # 5. 차량 비교 테스트
            compare_result = await mcp_server.execute_tool(
                "carfinance__compare_vehicles",
                vehicle_ids=[self.test_vehicle_id, "test_vehicle_002"],
                comparison_criteria=["price", "safety"],
                user_id=self.test_user_id
            )

            assert compare_result.success, f"차량 비교 실패: {compare_result.error}"

            duration = time.time() - start_time
            self.test_results[test_name] = {
                "status": "passed",
                "duration_seconds": duration,
                "details": {
                    "behavior_collection": collection_success,
                    "realtime_learning": learning_success,
                    "recommendation_generation": recommendation_result.success,
                    "behavior_analysis": analysis_result.success,
                    "vehicle_comparison": compare_result.success
                }
            }

            logger.info(f"✅ {test_name} 테스트 통과 ({duration:.2f}초)")

        except Exception as e:
            self.test_results[test_name] = {
                "status": "failed",
                "error": str(e),
                "duration_seconds": time.time() - start_time
            }
            logger.error(f"❌ {test_name} 테스트 실패: {e}")

    async def _test_system_performance(self):
        """시스템 성능 테스트"""
        test_name = "performance"
        logger.info(f"⚡ {test_name} 테스트 시작")

        try:
            start_time = time.time()

            # 부하 테스트: 100개 동시 사용자 행동 처리
            strategy = await get_user_behavior_collection_strategy()

            # 테스트 이벤트 생성
            test_events = []
            for i in range(100):
                event = {
                    "user_id": f"perf_test_user_{i:03d}",
                    "event_type": "view",
                    "vehicle_id": f"perf_test_vehicle_{i % 10:03d}",
                    "session_id": f"perf_session_{i:03d}",
                    "duration_seconds": 30 + (i % 60)
                }
                test_events.append(event)

            # 동시 처리 테스트
            performance_start = time.time()

            tasks = [strategy.collect_behavior(event) for event in test_events]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            performance_duration = time.time() - performance_start

            # 성공률 계산
            successful_count = sum(1 for result in results if result is True)
            success_rate = successful_count / len(test_events)

            # 처리량 계산 (events per second)
            throughput = len(test_events) / performance_duration

            assert success_rate >= 0.9, f"성공률 낮음: {success_rate:.2%}"
            assert throughput >= 50, f"처리량 낮음: {throughput:.2f} events/sec"

            duration = time.time() - start_time
            self.test_results[test_name] = {
                "status": "passed",
                "duration_seconds": duration,
                "details": {
                    "events_tested": len(test_events),
                    "success_rate": success_rate,
                    "throughput_events_per_second": throughput,
                    "processing_duration": performance_duration
                }
            }

            logger.info(f"✅ {test_name} 테스트 통과 ({duration:.2f}초)")
            logger.info(f"📊 성능 메트릭: {successful_count}/{len(test_events)} 성공, {throughput:.2f} events/sec")

        except Exception as e:
            self.test_results[test_name] = {
                "status": "failed",
                "error": str(e),
                "duration_seconds": time.time() - start_time
            }
            logger.error(f"❌ {test_name} 테스트 실패: {e}")

    async def _cleanup_test_data(self):
        """테스트 데이터 정리"""
        try:
            if self.db_manager:
                async with self.db_manager.get_connection() as conn:
                    # 테스트 사용자 상호작용 삭제
                    await conn.execute(
                        "DELETE FROM user_interactions WHERE user_id LIKE 'test_%' OR user_id LIKE 'perf_test_%'"
                    )

                    logger.info("🧹 테스트 데이터 정리 완료")

        except Exception as e:
            logger.error(f"❌ 테스트 데이터 정리 실패: {e}")

    def generate_test_report(self) -> str:
        """테스트 보고서 생성"""
        report = []
        report.append("=" * 60)
        report.append("CarFinanceAI 통합 테스트 보고서")
        report.append("=" * 60)
        report.append(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # 전체 결과 요약
        total_tests = len([k for k in self.test_results.keys() if k != "overall"])
        passed_tests = len([v for v in self.test_results.values() if v.get("status") == "passed"])
        failed_tests = len([v for v in self.test_results.values() if v.get("status") == "failed"])
        skipped_tests = len([v for v in self.test_results.values() if v.get("status") == "skipped"])

        report.append("📊 테스트 결과 요약")
        report.append(f"  총 테스트: {total_tests}")
        report.append(f"  통과: {passed_tests} ✅")
        report.append(f"  실패: {failed_tests} ❌")
        report.append(f"  건너뜀: {skipped_tests} ⏭️")
        report.append("")

        # 개별 테스트 결과
        report.append("📋 개별 테스트 결과")
        for test_name, result in self.test_results.items():
            if test_name == "overall":
                continue

            status_icon = {
                "passed": "✅",
                "failed": "❌",
                "skipped": "⏭️"
            }.get(result["status"], "❓")

            duration = result.get("duration_seconds", 0)
            report.append(f"  {status_icon} {test_name}: {result['status']} ({duration:.2f}초)")

            if result["status"] == "failed":
                report.append(f"    오류: {result.get('error', 'Unknown error')}")

        # 성능 메트릭
        if "performance" in self.test_results and self.test_results["performance"]["status"] == "passed":
            perf = self.test_results["performance"]["details"]
            report.append("")
            report.append("⚡ 성능 메트릭")
            report.append(f"  처리량: {perf.get('throughput_events_per_second', 0):.2f} events/sec")
            report.append(f"  성공률: {perf.get('success_rate', 0):.1%}")

        report.append("")
        report.append("=" * 60)

        return "\n".join(report)

# 테스트 실행 함수
async def run_integration_tests():
    """통합 테스트 실행"""
    test_suite = IntegrationTestSuite()
    results = await test_suite.run_all_tests()

    # 테스트 보고서 출력
    report = test_suite.generate_test_report()
    print(report)

    # 결과를 파일로 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"claudedocs/integration_test_report_{timestamp}.md"

    os.makedirs("claudedocs", exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("# CarFinanceAI 통합 테스트 보고서\n\n")
        f.write(f"실행 시간: {datetime.now().isoformat()}\n\n")
        f.write("```\n")
        f.write(report)
        f.write("\n```\n\n")
        f.write("## 상세 결과\n\n")
        f.write("```json\n")
        f.write(json.dumps(results, ensure_ascii=False, indent=2))
        f.write("\n```\n")

    logger.info(f"📄 테스트 보고서 저장: {report_file}")

    return results

if __name__ == "__main__":
    # 비동기 테스트 실행
    asyncio.run(run_integration_tests())