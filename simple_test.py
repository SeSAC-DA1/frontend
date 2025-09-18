"""
간단한 NCF 추천 시스템 테스트
"""
import requests
import json

def test_ncf_api():
    url = "http://localhost:8000/api/recommendations"

    # 테스트 사용자 1: 젊은 직장인
    test_user = {
        "user_profile": {
            "user_id": "test_young_pro",
            "age": 28,
            "income": 4500,
            "preferences": ["연비", "안전성"],
            "budget_range": {"max": 3500}
        },
        "recommendation_type": "ncf_hybrid",
        "limit": 5
    }

    print("NCF 추천 시스템 테스트 시작...")
    print("-" * 50)

    try:
        response = requests.post(url, json=test_user, timeout=10)

        if response.status_code == 200:
            data = response.json()
            recommendations = data.get('recommendations', [])
            metadata = data.get('metadata', {})

            print(f"성공! {len(recommendations)}개 추천 결과:")
            print(f"알고리즘: {metadata.get('algorithm', 'unknown')}")
            print(f"처리 시간: {metadata.get('processing_time_ms', 0)}ms")
            print(f"모드: {metadata.get('mode', 'unknown')}")
            print("-" * 50)

            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. 차량 ID: {rec.get('vehicle_id', 'unknown')}")
                print(f"   점수: {rec.get('score', 0):.3f}")
                print(f"   신뢰도: {rec.get('confidence', 0):.3f}")
                print(f"   이유: {', '.join(rec.get('reasons', []))}")
                print(f"   알고리즘: {rec.get('algorithm', 'unknown')}")
                print()

            # 품질 평가
            avg_score = sum(rec.get('score', 0) for rec in recommendations) / len(recommendations)
            avg_confidence = sum(rec.get('confidence', 0) for rec in recommendations) / len(recommendations)

            print("품질 평가:")
            print(f"  평균 점수: {avg_score:.3f}")
            print(f"  평균 신뢰도: {avg_confidence:.3f}")
            print(f"  다양성: {len(set(rec.get('algorithm', '') for rec in recommendations))}/1")

            return True

        else:
            print(f"API 오류: {response.status_code}")
            print(f"응답: {response.text}")
            return False

    except Exception as e:
        print(f"연결 오류: {e}")
        return False

if __name__ == "__main__":
    test_ncf_api()