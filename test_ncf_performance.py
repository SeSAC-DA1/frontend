"""
NCF 추천 시스템 성능 측정 및 검증
실제 NCF vs 기본 추천 시스템 비교 테스트
"""
import requests
import json
import time
import statistics
from typing import Dict, List
import pandas as pd

# 테스트 설정
BACKEND_URL = "http://localhost:8000"
TEST_USERS = [
    {
        "user_id": "test_young_professional",
        "age": 28,
        "income": 4500,
        "preferences": ["연비", "안전성"],
        "budget_range": {"max": 3500}
    },
    {
        "user_id": "test_family_user",
        "age": 35,
        "income": 6000,
        "preferences": ["가족용", "넓은 공간", "안전성"],
        "budget_range": {"max": 4500}
    },
    {
        "user_id": "test_luxury_user",
        "age": 45,
        "income": 8000,
        "preferences": ["럭셔리", "브랜드", "성능"],
        "budget_range": {"max": 7000}
    },
    {
        "user_id": "test_budget_user",
        "age": 24,
        "income": 3000,
        "preferences": ["가격", "연비"],
        "budget_range": {"max": 2500}
    },
    {
        "user_id": "test_eco_user",
        "age": 30,
        "income": 5500,
        "preferences": ["친환경", "전기차", "연비"],
        "budget_range": {"max": 5000}
    }
]

def test_recommendation_api(user_profile: Dict, limit: int = 10) -> Dict:
    """추천 API 테스트"""
    url = f"{BACKEND_URL}/api/recommendations"
    payload = {
        "user_profile": user_profile,
        "recommendation_type": "ncf_hybrid",
        "limit": limit
    }

    start_time = time.time()
    try:
        response = requests.post(url, json=payload, timeout=10)
        response_time = time.time() - start_time

        if response.status_code == 200:
            return {
                "success": True,
                "data": response.json(),
                "response_time": response_time,
                "status_code": 200
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "response_time": response_time,
                "status_code": response.status_code
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response_time": time.time() - start_time,
            "status_code": 0
        }

def analyze_recommendation_quality(recommendations: List[Dict], user_profile: Dict) -> Dict:
    """추천 품질 분석"""
    if not recommendations:
        return {"error": "추천 결과가 없습니다"}

    # 1. 다양성 점수 (서로 다른 차량 브랜드/모델)
    algorithms = set(rec.get('algorithm', 'unknown') for rec in recommendations)
    diversity_score = len(algorithms) / len(recommendations) if recommendations else 0

    # 2. 신뢰도 점수 평균
    confidence_scores = [rec.get('confidence', 0) for rec in recommendations]
    avg_confidence = statistics.mean(confidence_scores) if confidence_scores else 0

    # 3. 추천 점수 분포
    recommendation_scores = [rec.get('score', 0) for rec in recommendations]
    score_variance = statistics.variance(recommendation_scores) if len(recommendation_scores) > 1 else 0

    # 4. 사용자 선호도 매칭 분석
    user_preferences = user_profile.get('preferences', [])
    preference_matches = 0

    for rec in recommendations:
        reasons = rec.get('reasons', [])
        for reason in reasons:
            for pref in user_preferences:
                if pref in reason:
                    preference_matches += 1
                    break

    preference_match_rate = preference_matches / len(recommendations) if recommendations else 0

    return {
        "diversity_score": round(diversity_score, 3),
        "avg_confidence": round(avg_confidence, 3),
        "score_variance": round(score_variance, 3),
        "preference_match_rate": round(preference_match_rate, 3),
        "total_recommendations": len(recommendations),
        "avg_score": round(statistics.mean(recommendation_scores), 3) if recommendation_scores else 0
    }

def run_performance_test():
    """성능 테스트 실행"""
    print("🧠 NCF 추천 시스템 성능 테스트 시작")
    print("=" * 60)

    # 백엔드 상태 확인
    try:
        health_response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        health_data = health_response.json()
        print(f"백엔드 상태: {health_data.get('status', 'unknown')}")
        print(f"NCF 모델: {health_data.get('ncf_model', 'unknown')}")
        print("-" * 60)
    except Exception as e:
        print(f"⚠️ 백엔드 연결 실패: {e}")
        return

    # 각 사용자별 테스트
    all_results = []
    response_times = []

    for i, user in enumerate(TEST_USERS, 1):
        print(f"\n📊 테스트 {i}/5: {user['user_id']}")
        print(f"   나이: {user['age']}, 소득: {user['income']}, 선호: {user['preferences']}")

        # API 호출
        result = test_recommendation_api(user)
        response_times.append(result['response_time'])

        if result['success']:
            recommendations = result['data'].get('recommendations', [])
            metadata = result['data'].get('metadata', {})

            # 결과 분석
            quality = analyze_recommendation_quality(recommendations, user)

            print(f"   ✅ 성공 (응답시간: {result['response_time']:.3f}초)")
            print(f"   📈 추천 개수: {quality['total_recommendations']}")
            print(f"   🎯 평균 점수: {quality['avg_score']}")
            print(f"   🔍 신뢰도: {quality['avg_confidence']}")
            print(f"   💎 다양성: {quality['diversity_score']}")
            print(f"   ❤️ 선호도 매칭: {quality['preference_match_rate']}")
            print(f"   🤖 알고리즘: {metadata.get('algorithm', 'unknown')}")
            print(f"   🔧 모드: {metadata.get('mode', 'unknown')}")

            # 상위 3개 추천 결과 표시
            print("   🚗 상위 3개 추천:")
            for j, rec in enumerate(recommendations[:3], 1):
                print(f"      {j}. {rec.get('vehicle_id', 'unknown')} (점수: {rec.get('score', 0):.3f})")
                reasons = rec.get('reasons', [])[:2]  # 상위 2개 이유만
                if reasons:
                    print(f"         이유: {', '.join(reasons)}")

            all_results.append({
                'user_id': user['user_id'],
                'success': True,
                'response_time': result['response_time'],
                'quality': quality,
                'algorithm': metadata.get('algorithm', 'unknown'),
                'mode': metadata.get('mode', 'unknown')
            })

        else:
            print(f"   ❌ 실패: {result['error']}")
            print(f"   ⏱️ 응답시간: {result['response_time']:.3f}초")
            all_results.append({
                'user_id': user['user_id'],
                'success': False,
                'error': result['error'],
                'response_time': result['response_time']
            })

    # 전체 성능 요약
    print("\n" + "=" * 60)
    print("📊 전체 성능 요약")
    print("=" * 60)

    successful_tests = [r for r in all_results if r['success']]
    success_rate = len(successful_tests) / len(all_results) * 100

    print(f"성공률: {success_rate:.1f}% ({len(successful_tests)}/{len(all_results)})")
    print(f"평균 응답시간: {statistics.mean(response_times):.3f}초")
    print(f"최대 응답시간: {max(response_times):.3f}초")
    print(f"최소 응답시간: {min(response_times):.3f}초")

    if successful_tests:
        # 품질 지표 평균
        avg_scores = [r['quality']['avg_score'] for r in successful_tests]
        avg_confidence = [r['quality']['avg_confidence'] for r in successful_tests]
        avg_diversity = [r['quality']['diversity_score'] for r in successful_tests]
        avg_preference_match = [r['quality']['preference_match_rate'] for r in successful_tests]

        print(f"\n품질 지표 평균:")
        print(f"  🎯 추천 점수: {statistics.mean(avg_scores):.3f}")
        print(f"  🔍 신뢰도: {statistics.mean(avg_confidence):.3f}")
        print(f"  💎 다양성: {statistics.mean(avg_diversity):.3f}")
        print(f"  ❤️ 선호도 매칭: {statistics.mean(avg_preference_match):.3f}")

        # 알고리즘 분포
        algorithms = [r['algorithm'] for r in successful_tests]
        modes = [r['mode'] for r in successful_tests]

        print(f"\n사용된 알고리즘:")
        for algo in set(algorithms):
            count = algorithms.count(algo)
            print(f"  📘 {algo}: {count}회 ({count/len(algorithms)*100:.1f}%)")

        print(f"\n실행 모드:")
        for mode in set(modes):
            count = modes.count(mode)
            print(f"  ⚙️ {mode}: {count}회 ({count/len(modes)*100:.1f}%)")

    # NCF 성능 평가
    print("\n" + "=" * 60)
    print("🧠 NCF 성능 평가")
    print("=" * 60)

    if success_rate >= 90:
        print("✅ 우수: 추천 시스템이 안정적으로 작동하고 있습니다")
    elif success_rate >= 70:
        print("⚠️ 양호: 일부 개선이 필요합니다")
    else:
        print("❌ 주의: 시스템 안정성 점검이 필요합니다")

    avg_response = statistics.mean(response_times)
    if avg_response < 0.5:
        print("⚡ 응답속도: 매우 빠름 (0.5초 미만)")
    elif avg_response < 2.0:
        print("🚀 응답속도: 빠름 (2초 미만)")
    else:
        print("🐌 응답속도: 개선 필요 (2초 이상)")

    if successful_tests:
        avg_quality = statistics.mean([r['quality']['avg_score'] for r in successful_tests])
        if avg_quality >= 0.7:
            print("🎯 추천 품질: 높음 (0.7 이상)")
        elif avg_quality >= 0.5:
            print("📊 추천 품질: 보통 (0.5-0.7)")
        else:
            print("📉 추천 품질: 개선 필요 (0.5 미만)")

    print("\n🎉 테스트 완료!")

    # 결과를 CSV로 저장
    if all_results:
        df_results = []
        for result in all_results:
            if result['success']:
                row = {
                    'user_id': result['user_id'],
                    'success': result['success'],
                    'response_time': result['response_time'],
                    'algorithm': result['algorithm'],
                    'mode': result['mode'],
                    'avg_score': result['quality']['avg_score'],
                    'confidence': result['quality']['avg_confidence'],
                    'diversity': result['quality']['diversity_score'],
                    'preference_match': result['quality']['preference_match_rate']
                }
            else:
                row = {
                    'user_id': result['user_id'],
                    'success': result['success'],
                    'response_time': result['response_time'],
                    'error': result['error']
                }
            df_results.append(row)

        df = pd.DataFrame(df_results)
        df.to_csv('ncf_performance_test_results.csv', index=False, encoding='utf-8')
        print(f"📁 결과가 'ncf_performance_test_results.csv'에 저장되었습니다")

if __name__ == "__main__":
    run_performance_test()