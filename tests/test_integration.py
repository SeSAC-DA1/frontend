"""
서비스 연동 통합 테스트
Next.js ↔ FastAPI ↔ Academic Recommendation System
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Any

class ServiceIntegrationTester:
    """서비스 연동 통합 테스트"""

    def __init__(self):
        self.fastapi_url = "http://localhost:8000"
        self.nextjs_url = "http://localhost:3000"
        self.test_results = {}

    async def test_fastapi_health(self) -> bool:
        """FastAPI 서버 상태 확인"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.fastapi_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ FastAPI Health: {data}")
                        return True
                    else:
                        print(f"❌ FastAPI Health Check Failed: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ FastAPI 연결 실패: {e}")
            return False

    async def test_academic_recommendation_endpoint(self) -> bool:
        """학술 추천 엔드포인트 테스트"""
        try:
            test_request = {
                "user_profile": {
                    "user_id": "test_user_1",
                    "name": "김테스트",
                    "age": 30,
                    "income": 5000,
                    "preferences": ["연비", "안전성", "BMW"],
                    "purpose": "commute",
                    "budget_range": {"min": 3000, "max": 6000}
                },
                "recommendation_type": "academic_hybrid",
                "limit": 5
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.fastapi_url}/api/recommendations",
                    json=test_request,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Academic Recommendation API: {len(data.get('recommendations', []))} 추천 반환")
                        print(f"   알고리즘: {data.get('metadata', {}).get('algorithm', 'Unknown')}")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Recommendation API Failed: {response.status} - {error_text}")
                        return False

        except Exception as e:
            print(f"❌ Academic Recommendation 테스트 실패: {e}")
            return False

    async def test_nextjs_api_route(self) -> bool:
        """Next.js API Route 테스트"""
        try:
            test_request = {
                "userId": "test_user_1",
                "userProfile": {
                    "user_id": "test_user_1",
                    "name": "김테스트",
                    "age": 30,
                    "income": 5000,
                    "preferences": ["연비", "안전성"],
                    "budgetRange": {"min": 3000, "max": 6000}
                },
                "recommendationType": "personalized",
                "limit": 5
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.nextjs_url}/api/recommendations",
                    json=test_request,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Next.js API Route: {len(data.get('recommendations', []))} 추천 반환")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Next.js API Route Failed: {response.status} - {error_text}")
                        return False

        except Exception as e:
            print(f"❌ Next.js API Route 테스트 실패: {e}")
            return False

    async def test_end_to_end_flow(self) -> bool:
        """End-to-End 플로우 테스트"""
        print("\n🔄 End-to-End 플로우 테스트 시작...")

        # 1. 사용자 입력 시뮬레이션
        user_input = {
            "message": "30대 직장인, 연비 좋은 중형차 찾고 있어요. 예산 5000만원",
            "userId": "e2e_test_user"
        }

        try:
            # 2. Next.js → FastAPI 호출 체인 테스트
            async with aiohttp.ClientSession() as session:
                # Next.js API Route를 통한 추천 요청
                start_time = time.time()

                async with session.post(
                    f"{self.nextjs_url}/api/recommendations",
                    json={
                        "userId": user_input["userId"],
                        "userProfile": {
                            "age": 30,
                            "income": 5000,
                            "preferences": ["연비", "중형"],
                            "budgetRange": {"max": 5000}
                        },
                        "limit": 8
                    }
                ) as response:
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000

                    if response.status == 200:
                        data = await response.json()
                        recommendations = data.get("recommendations", [])

                        print(f"✅ E2E 테스트 성공!")
                        print(f"   추천 수: {len(recommendations)}")
                        print(f"   응답 시간: {response_time:.2f}ms")
                        print(f"   메타데이터: {data.get('metadata', {})}")

                        # 추천 결과 샘플 출력
                        if recommendations:
                            sample = recommendations[0]
                            print(f"   샘플 추천: {sample.get('vehicle_id', 'Unknown')} (점수: {sample.get('score', 0)})")

                        return True
                    else:
                        print(f"❌ E2E 테스트 실패: {response.status}")
                        return False

        except Exception as e:
            print(f"❌ E2E 테스트 오류: {e}")
            return False

    async def test_performance_benchmark(self) -> Dict[str, float]:
        """성능 벤치마크 테스트"""
        print("\n📊 성능 벤치마크 테스트...")

        test_scenarios = [
            {"name": "소규모 요청", "concurrent": 5, "requests": 20},
            {"name": "중간 규모 요청", "concurrent": 10, "requests": 50},
            {"name": "대규모 요청", "concurrent": 20, "requests": 100}
        ]

        results = {}

        for scenario in test_scenarios:
            print(f"\n🎯 {scenario['name']} 테스트 중...")

            async def single_request():
                try:
                    async with aiohttp.ClientSession() as session:
                        start = time.time()
                        async with session.post(
                            f"{self.nextjs_url}/api/recommendations",
                            json={
                                "userId": f"perf_test_{time.time()}",
                                "userProfile": {
                                    "age": 30,
                                    "income": 5000,
                                    "preferences": ["연비"],
                                    "budgetRange": {"max": 5000}
                                },
                                "limit": 5
                            }
                        ) as response:
                            end = time.time()
                            return (end - start) * 1000, response.status == 200
                except:
                    return None, False

            # 동시 요청 실행
            start_time = time.time()
            tasks = []

            for batch in range(0, scenario["requests"], scenario["concurrent"]):
                batch_tasks = [single_request() for _ in range(min(scenario["concurrent"], scenario["requests"] - batch))]
                batch_results = await asyncio.gather(*batch_tasks)
                tasks.extend(batch_results)

            end_time = time.time()

            # 결과 분석
            response_times = [t[0] for t in tasks if t[0] is not None]
            success_count = sum(1 for t in tasks if t[1])

            if response_times:
                avg_response = sum(response_times) / len(response_times)
                min_response = min(response_times)
                max_response = max(response_times)
                success_rate = (success_count / len(tasks)) * 100

                results[scenario["name"]] = {
                    "평균 응답시간": avg_response,
                    "최소 응답시간": min_response,
                    "최대 응답시간": max_response,
                    "성공률": success_rate,
                    "총 처리시간": (end_time - start_time) * 1000
                }

                print(f"   평균 응답시간: {avg_response:.2f}ms")
                print(f"   성공률: {success_rate:.1f}%")
            else:
                print(f"   ❌ 모든 요청 실패")

        return results

    async def run_all_tests(self) -> Dict[str, Any]:
        """모든 테스트 실행"""
        print("CarFin AI Service Integration Test Start")
        print("=" * 60)

        test_results = {}

        # 1. 기본 연결 테스트
        print("\n1️⃣ 기본 서비스 연결 테스트")
        test_results["fastapi_health"] = await self.test_fastapi_health()

        # 2. FastAPI 추천 엔드포인트 테스트
        print("\n2️⃣ FastAPI 추천 엔드포인트 테스트")
        test_results["fastapi_recommendation"] = await self.test_academic_recommendation_endpoint()

        # 3. Next.js API Route 테스트
        print("\n3️⃣ Next.js API Route 테스트")
        test_results["nextjs_api_route"] = await self.test_nextjs_api_route()

        # 4. End-to-End 테스트
        print("\n4️⃣ End-to-End 플로우 테스트")
        test_results["end_to_end"] = await self.test_end_to_end_flow()

        # 5. 성능 벤치마크
        print("\n5️⃣ 성능 벤치마크 테스트")
        test_results["performance"] = await self.test_performance_benchmark()

        # 결과 요약
        print("\n" + "=" * 60)
        print("🎯 테스트 결과 요약")
        print("=" * 60)

        success_count = sum(1 for k, v in test_results.items() if k != "performance" and v)
        total_tests = len([k for k in test_results.keys() if k != "performance"])

        print(f"기본 테스트: {success_count}/{total_tests} 성공")

        if test_results.get("performance"):
            print("\n📊 성능 결과:")
            for scenario, metrics in test_results["performance"].items():
                print(f"  {scenario}: {metrics.get('평균 응답시간', 0):.2f}ms (성공률: {metrics.get('성공률', 0):.1f}%)")

        # 전체 상태 평가
        if success_count == total_tests:
            print("\n✅ 모든 서비스 연동이 정상 작동합니다!")
            overall_status = "PASS"
        else:
            print("\n⚠️ 일부 서비스에 문제가 있습니다.")
            overall_status = "PARTIAL"

        test_results["overall_status"] = overall_status
        return test_results

async def main():
    """메인 테스트 실행"""
    tester = ServiceIntegrationTester()
    results = await tester.run_all_tests()

    # 결과를 JSON 파일로 저장
    with open("integration_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n📄 상세 결과가 'integration_test_results.json'에 저장되었습니다.")

    return results["overall_status"] == "PASS"

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)