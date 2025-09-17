#!/usr/bin/env python3
"""
CarFin AI 사용자 여정 테스트 스크립트
실시간 협업 필터링 학습 시스템의 전체 플로우를 테스트합니다.
"""

import requests
import json
import time
from datetime import datetime

# API 베이스 URL
BASE_URL = "http://localhost:8000"

def print_step(step_num, description):
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {description}")
    print(f"{'='*60}")

def test_user_registration():
    """사용자 등록 테스트"""
    print_step(1, "사용자 등록")

    user_data = {
        "full_name": "김테스트",
        "email": "kim.test@carfin.ai",
        "age": 32,
        "phone": "010-1234-5678"
    }

    response = requests.post(f"{BASE_URL}/api/users/register", json=user_data)

    if response.status_code == 200:
        result = response.json()
        user_id = result["user_id"]
        print(f"✅ 사용자 등록 성공")
        print(f"   사용자 ID: {user_id}")
        print(f"   이름: {result['user_data']['full_name']}")
        print(f"   이메일: {result['user_data']['email']}")
        return user_id
    else:
        print(f"❌ 사용자 등록 실패: {response.status_code}")
        return None

def test_user_preferences(user_id):
    """사용자 선호도 설정 테스트"""
    print_step(2, "사용자 선호도 설정")

    preferences_data = {
        "user_id": user_id,
        "budget_max": 4000,
        "family_size": 4,
        "usage_purpose": "family"
    }

    response = requests.post(f"{BASE_URL}/api/users/{user_id}/preferences", json=preferences_data)

    if response.status_code == 200:
        result = response.json()
        print(f"✅ 선호도 설정 성공")
        print(f"   최대 예산: {preferences_data['budget_max']}만원")
        print(f"   가족 구성원: {preferences_data['family_size']}명")
        print(f"   사용 목적: {preferences_data['usage_purpose']}")
        return True
    else:
        print(f"❌ 선호도 설정 실패: {response.status_code}")
        return False

def test_initial_consultation():
    """초기 차량 추천 테스트"""
    print_step(3, "초기 차량 추천 요청")

    consultation_data = {
        "budget_range": [2000, 5000],
        "year_range": [2019, 2024],
        "fuel_type": "hybrid",
        "body_type": "suv",
        "preferred_model": ""
    }

    response = requests.post(f"{BASE_URL}/api/consultation/full", json=consultation_data)

    if response.status_code == 200:
        result = response.json()
        vehicles = result.get("vehicles", [])
        print(f"✅ 초기 추천 성공")
        print(f"   추천 차량 수: {len(vehicles)}대")

        for i, vehicle in enumerate(vehicles[:3]):
            print(f"   {i+1}. {vehicle['brand']} {vehicle['model']} ({vehicle['year']}년)")
            print(f"      가격: {vehicle['price']:,}만원, 매칭도: {vehicle['match_score']}%")

        return vehicles
    else:
        print(f"❌ 초기 추천 실패: {response.status_code}")
        return []

def test_user_interactions(user_id, vehicles):
    """사용자 상호작용 테스트"""
    print_step(4, "사용자 상호작용 시뮬레이션")

    interactions = []
    interaction_types = ['click', 'save', 'view', 'click', 'save']

    for i, vehicle in enumerate(vehicles[:5]):
        interaction_type = interaction_types[i % len(interaction_types)]

        interaction_data = {
            "user_id": user_id,
            "vehicle_id": vehicle["id"],
            "interaction_type": interaction_type,
            "timestamp": datetime.now().isoformat()
        }

        response = requests.post(f"{BASE_URL}/api/users/interaction", json=interaction_data)

        if response.status_code == 200:
            result = response.json()
            interactions.append(vehicle["id"])
            print(f"✅ 상호작용 {i+1}: {vehicle['brand']} {vehicle['model']} - {interaction_type}")
            print(f"   총 상호작용 수: {result['total_interactions']}")
        else:
            print(f"❌ 상호작용 {i+1} 실패: {response.status_code}")

        time.sleep(0.5)  # 실제 사용자 행동 시뮬레이션

    return interactions

def test_adaptive_recommendations(user_id, interactions):
    """적응형 추천 테스트"""
    print_step(5, "적응형 추천 시스템 테스트")

    adaptive_data = {
        "user_id": user_id,
        "interactions": interactions,
        "current_preferences": {
            "budget_max": 4000,
            "family_size": 4,
            "usage_purpose": "family"
        }
    }

    response = requests.post(f"{BASE_URL}/api/consultation/adaptive", json=adaptive_data)

    if response.status_code == 200:
        result = response.json()
        vehicles = result.get("vehicles", [])
        metadata = result.get("metadata", {})

        print(f"✅ 적응형 추천 성공")
        print(f"   학습 상태: {metadata.get('learning_status', 'unknown')}")
        print(f"   상호작용 횟수: {metadata.get('interaction_count', 0)}")
        print(f"   추천 차량 수: {len(vehicles)}대")

        print(f"\n🎯 상위 3개 추천 차량:")
        for i, vehicle in enumerate(vehicles[:3]):
            print(f"   {i+1}순위: {vehicle['brand']} {vehicle['model']}")
            print(f"      매칭도: {vehicle['match_score']}% (순위: #{vehicle['ranking_position']})")
            print(f"      AI 점수 - 협업필터링: {vehicle['agent_scores']['collaborative_filtering']}%")
            print(f"               시장분석: {vehicle['agent_scores']['market_analysis']}%")
            print(f"               개인맞춤: {vehicle['agent_scores']['personal_preference']}%")
            print(f"      추천이유: {', '.join(vehicle['match_reasons'][:3])}")
            print()

        return vehicles[:3]
    else:
        print(f"❌ 적응형 추천 실패: {response.status_code}")
        return []

def test_system_health():
    """시스템 상태 확인"""
    print_step(0, "시스템 상태 확인")

    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ 백엔드 서버 정상 작동")
        else:
            print(f"⚠️ 백엔드 서버 응답 이상: {response.status_code}")

        # 프론트엔드 확인
        try:
            frontend_response = requests.get("http://localhost:3001", timeout=5)
            if frontend_response.status_code == 200:
                print("✅ 프론트엔드 서버 정상 작동 (포트: 3001)")
            else:
                print(f"⚠️ 프론트엔드 서버 응답 이상: {frontend_response.status_code}")
        except:
            print("❌ 프론트엔드 서버 연결 실패")

    except Exception as e:
        print(f"❌ 시스템 연결 실패: {e}")
        return False

    return True

def main():
    """전체 사용자 여정 테스트 실행"""
    print("🚗 CarFin AI 실시간 협업 필터링 학습 시스템")
    print("사용자 여정 통합 테스트를 시작합니다...\n")

    # 시스템 상태 확인
    if not test_system_health():
        print("❌ 시스템 연결 실패. 테스트를 중단합니다.")
        return

    # 1. 사용자 등록
    user_id = test_user_registration()
    if not user_id:
        print("❌ 사용자 등록 실패. 테스트를 중단합니다.")
        return

    # 2. 사용자 선호도 설정
    if not test_user_preferences(user_id):
        print("❌ 선호도 설정 실패. 테스트를 중단합니다.")
        return

    # 3. 초기 차량 추천
    vehicles = test_initial_consultation()
    if not vehicles:
        print("❌ 초기 추천 실패. 테스트를 중단합니다.")
        return

    # 4. 사용자 상호작용 시뮬레이션
    interactions = test_user_interactions(user_id, vehicles)
    if not interactions:
        print("❌ 상호작용 테스트 실패. 테스트를 중단합니다.")
        return

    # 5. 적응형 추천 (실시간 학습 결과)
    final_vehicles = test_adaptive_recommendations(user_id, interactions)

    # 테스트 완료 요약
    print_step("완료", "사용자 여정 테스트 결과")

    if final_vehicles:
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("\n📊 테스트 결과 요약:")
        print(f"   • 등록된 사용자 ID: {user_id}")
        print(f"   • 기록된 상호작용 수: {len(interactions)}")
        print(f"   • 최종 추천 차량 수: {len(final_vehicles)}")
        print(f"   • 최고 매칭 점수: {max(v['match_score'] for v in final_vehicles)}%")

        print("\n🔗 다음 단계:")
        print("   1. 브라우저에서 http://localhost:3001 접속")
        print("   2. 회원가입 후 차량 검색 실행")
        print("   3. 여러 차량 클릭/저장하여 학습 데이터 누적")
        print("   4. '최종 3차량 비교 분석' 버튼으로 상세 비교")

    else:
        print("❌ 일부 테스트가 실패했습니다. 로그를 확인해주세요.")

if __name__ == "__main__":
    main()