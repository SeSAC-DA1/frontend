"""
Test the new Gemini Multi-Agent System
"""
import os
from agents.gemini_multi_agent import gemini_multi_agent

# Set API key
os.environ["GOOGLE_API_KEY"] = "AIzaSyArwWj3_TDhSuCVXYoDzVGM2MW26-5UqbU"

def test_new_gemini_system():
    """Test the new Gemini multi-agent system"""

    user_message = "30대 직장인입니다. 출퇴근용 차량을 찾고 있어요. 예산은 3000만원 정도입니다."

    print("=== Testing New Gemini Multi-Agent System ===")
    print(f"User message: {user_message}")
    print("\n" + "="*50)

    # Test the new system
    result = gemini_multi_agent.get_vehicle_recommendations(user_message)

    if result["status"] == "success":
        print("✅ SUCCESS: New Gemini Multi-Agent System works!")
        print(f"Workflow type: {result['workflow_type']}")
        print(f"Agents used: {result['agents_collaboration']['agents_used']}")
        print(f"Communication count: {result['agents_collaboration']['communication_count']}")

        # Print agent responses
        multi_agent_result = result.get("multi_agent_result", {})
        agent_responses = multi_agent_result.get("agent_responses", {})

        if agent_responses:
            print("\n=== Agent Responses ===")
            for agent, response in agent_responses.items():
                print(f"\n--- {agent.upper()} ---")
                print(response[:200] + "..." if len(response) > 200 else response)

        return True
    else:
        print(f"❌ ERROR: {result.get('message', 'Unknown error')}")
        return False

if __name__ == "__main__":
    success = test_new_gemini_system()
    if success:
        print("\n🎉 New Gemini Multi-Agent System is ready to replace CrewAI!")
    else:
        print("\n💥 System needs more work...")