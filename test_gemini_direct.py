"""
Direct Gemini Test - Bypass CrewAI issues
"""
import os
import json
from agents.llm_provider import get_llm_response, LLMProvider

# Set API key
os.environ["GOOGLE_API_KEY"] = "AIzaSyArwWj3_TDhSuCVXYoDzVGM2MW26-5UqbU"

def test_direct_gemini():
    """Test direct Gemini calls without CrewAI"""

    user_message = "30대 직장인입니다. 출퇴근용 차량을 찾고 있어요. 예산은 3000만원 정도입니다."

    # Test user profile parsing
    print("=== 1. User Profile Parsing ===")
    parse_prompt = f"""
    다음 사용자 메시지를 분석하여 차량 구매 요구사항을 JSON 형태로 추출해주세요.

    사용자 메시지: "{user_message}"

    다음 형태의 JSON으로 응답해주세요:
    {{
        "budget_max": 예산 상한선 (만원, 숫자만),
        "age_group": "20대" 또는 "30대" 등,
        "purpose": "출퇴근", "가족용", "레저" 등 주요 용도,
        "category": "Compact", "Mid-size", "SUV", "Luxury" 중 선호 카테고리,
        "fuel_type": "Gasoline", "Hybrid", "Electric" 중 연료 선호,
        "priorities": ["연비", "안전", "디자인", "가격"] 등 우선순위 배열,
        "experience": "첫차", "경험있음" 등 구매경험
    }}
    """

    response = get_llm_response(
        messages=[{"role": "user", "content": parse_prompt}],
        providers=[LLMProvider.GEMINI_PRO],
        response_format="json"
    )

    if response.success:
        user_profile = json.loads(response.content)
        print(f"✅ User profile parsed: {user_profile}")
    else:
        print(f"❌ Profile parsing failed: {response.error}")
        return

    # Test vehicle recommendation
    print("\n=== 2. Vehicle Recommendation ===")
    recommendation_prompt = f"""
    사용자 프로필: {json.dumps(user_profile, ensure_ascii=False)}

    당신은 차량 추천 전문가입니다. 위 사용자 프로필을 바탕으로 다음을 수행해주세요:

    1. 사용자 요구사항에 맞는 차량 3개 추천
    2. 각 차량의 장점과 추천 이유 설명
    3. 가격, 연비, 안전성 등 핵심 정보 제공

    응답 형태:
    - 추천 차량 1: [차량명] - [가격] - [핵심 장점과 추천 이유]
    - 추천 차량 2: [차량명] - [가격] - [핵심 장점과 추천 이유]
    - 추천 차량 3: [차량명] - [가격] - [핵심 장점과 추천 이유]
    """

    response = get_llm_response(
        messages=[{"role": "user", "content": recommendation_prompt}],
        providers=[LLMProvider.GEMINI_PRO]
    )

    if response.success:
        print(f"✅ Vehicle recommendations: {response.content}")
    else:
        print(f"❌ Recommendation failed: {response.error}")

    # Test finance consultation
    print("\n=== 3. Finance Consultation ===")
    finance_prompt = f"""
    선택된 차량: 현대 아반떼 (약 2500만원)
    사용자 예산: {user_profile.get('budget_max', 3000)}만원

    당신은 자동차 금융 상담 전문가입니다. 이 차량에 대해 다음 금융 옵션들을 비교해주세요:

    1. 현금 일시불
    2. 은행 대출 (5년 기준)
    3. 캐피탈 할부 (5년 기준)
    4. 리스 (4년 기준)

    각 옵션별로 월 납부액, 총 지급 비용, 장단점을 설명해주세요.
    """

    response = get_llm_response(
        messages=[{"role": "user", "content": finance_prompt}],
        providers=[LLMProvider.GEMINI_PRO]
    )

    if response.success:
        print(f"✅ Finance consultation: {response.content}")
    else:
        print(f"❌ Finance consultation failed: {response.error}")

if __name__ == "__main__":
    test_direct_gemini()