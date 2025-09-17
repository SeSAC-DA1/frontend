"""
Simplified CarFin FastAPI Backend for testing
"""
import os
import pandas as pd
import uuid
import hashlib
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CarFin AI",
    description="CrewAI 멀티에이전트 차량 추천 및 금융 상담 시스템",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class UserRequest(BaseModel):
    message: str = Field(..., description="사용자의 차량 추천 요청 메시지")
    user_id: Optional[str] = Field(None, description="사용자 ID (선택적)")

class CarSelection(BaseModel):
    car_id: str = Field(..., description="선택된 차량 ID")
    user_budget: int = Field(..., description="사용자 예산 (만원 단위)")

# New models for chatbot integration
class UserRegistration(BaseModel):
    full_name: str = Field(..., description="사용자 전체 이름")
    email: str = Field(..., description="이메일 주소")
    age: int = Field(..., description="나이")
    phone: Optional[str] = Field(None, description="전화번호 (선택적)")

class UserPreferences(BaseModel):
    user_id: str = Field(..., description="사용자 ID")
    budget_min: Optional[int] = Field(None, description="최소 예산 (만원)")
    budget_max: Optional[int] = Field(None, description="최대 예산 (만원)")
    fuel_type: Optional[str] = Field(None, description="연료 타입")
    category: Optional[str] = Field(None, description="차량 카테고리")
    transmission: Optional[str] = Field(None, description="변속기 타입")
    family_size: Optional[int] = Field(None, description="가족 구성원 수")
    usage_purpose: Optional[str] = Field(None, description="사용 목적")

class ChatMessage(BaseModel):
    user_id: str = Field(..., description="사용자 ID")
    message: str = Field(..., description="채팅 메시지")
    context: Optional[Dict[str, Any]] = Field(None, description="대화 컨텍스트")

# Global agent system - lazy load
_carfin_agents = None

# In-memory storage for demo (would use database in production)
users_db = {}  # user_id -> user_data
preferences_db = {}  # user_id -> preferences
conversations_db = {}  # user_id -> conversation_history

def get_agents():
    global _carfin_agents
    if _carfin_agents is None:
        try:
            from agents.crew_setup import carfin_agents
            _carfin_agents = carfin_agents
            logger.info("Agents loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load agents: {e}")
            raise
    return _carfin_agents

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "CarFin AI Backend is running",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        agents = get_agents()
        agents_status = "initialized" if agents.recommendation_engine else "error"
        
        return {
            "status": "healthy",
            "agents": agents_status,
            "database": "connected" if agents.recommendation_engine.engine else "disconnected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.post("/api/recommend")
async def get_car_recommendation(request: UserRequest):
    """Get personalized car recommendations"""
    try:
        logger.info(f"Processing recommendation request: {request.message[:50]}...")
        
        agents = get_agents()
        result = agents.get_vehicle_recommendations(request.message)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        return result
        
    except Exception as e:
        logger.error(f"Recommendation request failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"차량 추천 중 오류가 발생했습니다: {str(e)}"
        )

@app.post("/api/finance")
async def get_finance_options(selection: CarSelection):
    """Get finance consultation for selected car"""
    try:
        logger.info(f"Processing finance consultation for car {selection.car_id}")
        
        agents = get_agents()
        result = agents.get_finance_consultation(
            selection.car_id, 
            selection.user_budget
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        
        return result
        
    except Exception as e:
        logger.error(f"Finance consultation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"금융 상담 중 오류가 발생했습니다: {str(e)}"
        )

@app.get("/api/cars/{car_id}")
async def get_car_details(car_id: int):
    """Get detailed information about a specific car"""
    try:
        agents = get_agents()
        car_details = agents.recommendation_engine.get_car_details(car_id)
        
        if not car_details:
            raise HTTPException(status_code=404, detail="차량 정보를 찾을 수 없습니다")
        
        return {
            "status": "success",
            "car": car_details
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get car details: {e}")
        raise HTTPException(status_code=500, detail="차량 정보 조회 중 오류가 발생했습니다")

# New API endpoints for chatbot integration

@app.post("/api/users/register")
async def register_user(user_data: UserRegistration):
    """Register a new user for the chatbot system"""
    try:
        # Generate user ID
        user_id = str(uuid.uuid4())
        
        # Check if email already exists
        for existing_user in users_db.values():
            if existing_user.get('email') == user_data.email:
                raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다")
        
        # Store user data
        users_db[user_id] = {
            "user_id": user_id,
            "full_name": user_data.full_name,
            "email": user_data.email,
            "age": user_data.age,
            "phone": user_data.phone,
            "created_at": pd.Timestamp.now().isoformat()
        }
        
        logger.info(f"New user registered: {user_data.full_name} ({user_id})")
        
        return {
            "status": "success",
            "message": "회원가입이 완료되었습니다",
            "user_id": user_id,
            "user_data": users_db[user_id]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User registration failed: {e}")
        raise HTTPException(status_code=500, detail="회원가입 중 오류가 발생했습니다")

@app.post("/api/users/{user_id}/preferences")
async def save_user_preferences(user_id: str, preferences: UserPreferences):
    """Save user preferences for vehicle recommendations"""
    try:
        # Verify user exists
        if user_id not in users_db:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # Store preferences
        preferences_db[user_id] = {
            "user_id": user_id,
            "budget_min": preferences.budget_min,
            "budget_max": preferences.budget_max,
            "fuel_type": preferences.fuel_type,
            "category": preferences.category,
            "transmission": preferences.transmission,
            "family_size": preferences.family_size,
            "usage_purpose": preferences.usage_purpose,
            "updated_at": pd.Timestamp.now().isoformat()
        }
        
        logger.info(f"Preferences saved for user {user_id}")
        
        return {
            "status": "success",
            "message": "선호도가 저장되었습니다",
            "preferences": preferences_db[user_id]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save preferences: {e}")
        raise HTTPException(status_code=500, detail="선호도 저장 중 오류가 발생했습니다")

@app.get("/api/users/{user_id}")
async def get_user_info(user_id: str):
    """Get user information"""
    try:
        if user_id not in users_db:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        user_data = users_db[user_id]
        preferences = preferences_db.get(user_id, {})
        
        return {
            "status": "success",
            "user": user_data,
            "preferences": preferences
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        raise HTTPException(status_code=500, detail="사용자 정보 조회 중 오류가 발생했습니다")

@app.post("/api/chat")
async def chat_consultation(chat_request: ChatMessage):
    """Real-time chat consultation with AI agents"""
    try:
        user_id = chat_request.user_id
        message = chat_request.message
        
        # Verify user exists
        if user_id not in users_db:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        # Get user data and preferences
        user_data = users_db[user_id]
        preferences = preferences_db.get(user_id, {})
        
        # Initialize conversation history if not exists
        if user_id not in conversations_db:
            conversations_db[user_id] = []
        
        # Add user message to conversation history
        conversations_db[user_id].append({
            "role": "user",
            "message": message,
            "timestamp": pd.Timestamp.now().isoformat()
        })
        
        # Create comprehensive context for AI agents
        context_message = f"""
        사용자 정보:
        - 이름: {user_data['full_name']}
        - 나이: {user_data['age']}세
        
        선호도 정보:
        - 예산: {preferences.get('budget_min', '미지정')}만원 ~ {preferences.get('budget_max', '미지정')}만원
        - 연료타입: {preferences.get('fuel_type', '미지정')}
        - 차량카테고리: {preferences.get('category', '미지정')}
        - 가족구성원: {preferences.get('family_size', '미지정')}명
        - 사용목적: {preferences.get('usage_purpose', '미지정')}
        
        사용자 메시지: {message}
        
        위 정보를 바탕으로 맞춤형 상담을 제공해주세요.
        """
        
        # Get AI agent response
        agents = get_agents()
        ai_response = agents.get_vehicle_recommendations(context_message)
        
        # Add AI response to conversation history
        conversations_db[user_id].append({
            "role": "assistant",
            "message": ai_response.get('agent_response', ''),
            "timestamp": pd.Timestamp.now().isoformat(),
            "ml_data": ai_response.get('ml_recommendations', [])
        })
        
        logger.info(f"Chat consultation completed for user {user_id}")
        
        return {
            "status": "success",
            "response": ai_response.get('agent_response', ''),
            "ml_recommendations": ai_response.get('ml_recommendations', []),
            "conversation_id": len(conversations_db[user_id])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat consultation failed: {e}")
        raise HTTPException(status_code=500, detail="AI 상담 중 오류가 발생했습니다")

@app.get("/api/users/{user_id}/conversations")
async def get_conversation_history(user_id: str):
    """Get conversation history for a user"""
    try:
        if user_id not in users_db:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        conversations = conversations_db.get(user_id, [])
        
        return {
            "status": "success",
            "conversations": conversations,
            "total": len(conversations)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversations: {e}")
        raise HTTPException(status_code=500, detail="대화 기록 조회 중 오류가 발생했습니다")

if __name__ == "__main__":
    import uvicorn
    
    # Backend runs on port 8000, frontend on 5000 for Replit webview
    port = int(os.environ.get("PORT", 8000))
    
    logger.info(f"Starting CarFin AI server on port {port}")
    
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload to avoid issues
        log_level="info"
    )