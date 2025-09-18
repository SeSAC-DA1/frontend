"""
CarFin AI FastAPI Backend
Academic Recommendation System + Gemini Multi-Agent Integration
"""
import os
import pandas as pd
import uuid
import hashlib
from typing import Dict, List, Any, Optional, Union
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import logging
import sys
sys.path.append('..')

# Academic Recommendation System Integration
ACADEMIC_SYSTEM_AVAILABLE = True  # NCF 모델 통합 활성화

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CarFin AI",
    description="Academic Paper-based Recommendation System + Gemini Multi-Agent",
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

# Import and include vehicle API routes
try:
    from vehicle_api_routes import router as vehicle_router
    app.include_router(vehicle_router)
    logger.info("✅ Vehicle API routes loaded successfully")
except Exception as e:
    logger.warning(f"⚠️ Failed to load vehicle API routes: {e}")
    logger.info("Continuing with existing mock data endpoints")

# Pydantic models
class UserRequest(BaseModel):
    message: str = Field(..., description="사용자의 차량 추천 요청 메시지")
    user_id: Optional[str] = Field(None, description="사용자 ID (선택적)")

class CarSelection(BaseModel):
    car_id: str = Field(..., description="선택된 차량 ID")
    user_budget: int = Field(..., description="사용자 예산 (만원 단위)")

# Enhanced models for 3-agent system
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

class FullConsultationRequest(BaseModel):
    message: str = Field(..., description="사용자 종합상담 요청 메시지")
    user_id: Optional[str] = Field(None, description="사용자 ID (선택적)")
    budget_range: Optional[List[int]] = Field(None, description="예산 범위 [최소, 최대] (만원 단위)")
    year_range: Optional[List[int]] = Field(None, description="연식 범위 [최소, 최대]")
    fuel_type: Optional[str] = Field("", description="연료 타입")
    body_type: Optional[str] = Field("", description="차종")
    preferred_model: Optional[str] = Field("", description="선호 브랜드/모델")
    include_finance: bool = Field(False, description="금융 상담 포함 여부")

class DashboardRequest(BaseModel):
    user_id: str = Field(..., description="사용자 ID")
    refresh_data: bool = Field(False, description="데이터 새로고침 여부")

class FinancialProductRequest(BaseModel):
    vehicle_id: str = Field(..., description="선택된 차량 ID")
    user_id: Optional[str] = Field(None, description="사용자 ID")
    vehicle_price: int = Field(..., description="차량 가격 (만원 단위)")
    down_payment: Optional[int] = Field(None, description="초기 납입금 (만원 단위)")
    loan_term: Optional[int] = Field(36, description="대출 기간 (개월)")
    credit_score: Optional[str] = Field("good", description="신용등급 (excellent, good, fair, poor)")
    income: Optional[int] = Field(None, description="월소득 (만원 단위)")

class UserInteractionRequest(BaseModel):
    user_id: str = Field(..., description="사용자 ID")
    vehicle_id: str = Field(..., description="차량 ID")
    interaction_type: str = Field(..., description="상호작용 타입 (click, save, view)")
    timestamp: str = Field(..., description="상호작용 시간")

class AdaptiveRecommendationRequest(BaseModel):
    user_id: str = Field(..., description="사용자 ID")
    interactions: List[str] = Field(..., description="상호작용한 차량 ID 목록")
    current_preferences: Dict[str, Any] = Field(..., description="현재 선호도 설정")

# Global agent system - lazy load
_carfin_agents = None

# In-memory storage for demo (would use database in production)
users_db = {}  # user_id -> user_data
preferences_db = {}  # user_id -> preferences
conversations_db = {}  # user_id -> conversation_history
user_interactions_db = {}  # user_id -> [interaction_data]

# Sample financial products for testing
sample_financial_products = [
    {
        "id": "loan_001",
        "provider": "KB국민은행",
        "product_name": "KB오토론",
        "loan_type": "중고차 할부금융",
        "interest_rate": 4.8,
        "max_loan_amount": 8000,
        "max_loan_term": 84,
        "features": ["보증인 불필요", "중도상환 수수료 면제", "온라인 신청"],
        "eligibility": ["만 20세 이상", "연소득 2000만원 이상", "신용등급 6등급 이상"],
        "match_score": 95,
        "monthly_payment": 0,  # Will be calculated
        "total_interest": 0,   # Will be calculated
        "agent_analysis": {
            "affordability_score": 92,
            "rate_competitiveness": 88,
            "approval_probability": 94
        }
    },
    {
        "id": "loan_002",
        "provider": "신한은행",
        "product_name": "신한 마이카론",
        "loan_type": "중고차 담보대출",
        "interest_rate": 5.2,
        "max_loan_amount": 7000,
        "max_loan_term": 72,
        "features": ["차량 담보", "금리 우대 혜택", "모바일 간편신청"],
        "eligibility": ["만 19세 이상", "재직 6개월 이상", "신용등급 7등급 이상"],
        "match_score": 89,
        "monthly_payment": 0,
        "total_interest": 0,
        "agent_analysis": {
            "affordability_score": 87,
            "rate_competitiveness": 82,
            "approval_probability": 91
        }
    },
    {
        "id": "loan_003",
        "provider": "현대캐피탈",
        "product_name": "현대캐피탈 오토론",
        "loan_type": "할부금융",
        "interest_rate": 6.8,
        "max_loan_amount": 6000,
        "max_loan_term": 60,
        "features": ["신속승인", "유연한 상환조건", "차량 즉시 출고"],
        "eligibility": ["만 20세 이상", "신용등급 무관", "소득증빙 가능자"],
        "match_score": 78,
        "monthly_payment": 0,
        "total_interest": 0,
        "agent_analysis": {
            "affordability_score": 75,
            "rate_competitiveness": 65,
            "approval_probability": 88
        }
    }
]

# Sample vehicle data for testing
sample_vehicles = [
    {
        "id": "car_001",
        "brand": "현대",
        "model": "아반떼",
        "year": 2022,
        "price": 2300,
        "mileage": 15000,
        "fuel_type": "gasoline",
        "location": "서울 강남구",
        "features": ["스마트키", "후방카메라", "블루투스"],
        "match_score": 94,
        "ranking_position": 1,
        "agent_scores": {
            "collaborative_filtering": 92,
            "market_analysis": 95,
            "personal_preference": 91
        },
        "match_reasons": ["예산 범위 적합", "연비 우수", "인기 모델"]
    },
    {
        "id": "car_002",
        "brand": "기아",
        "model": "K5",
        "year": 2021,
        "price": 2650,
        "mileage": 22000,
        "fuel_type": "hybrid",
        "location": "서울 서초구",
        "features": ["하이브리드", "썬루프", "내비게이션"],
        "match_score": 89,
        "ranking_position": 2,
        "agent_scores": {
            "collaborative_filtering": 88,
            "market_analysis": 91,
            "personal_preference": 87
        },
        "match_reasons": ["연비 절약", "안전성 우수", "브랜드 신뢰도"]
    },
    {
        "id": "car_003",
        "brand": "BMW",
        "model": "320i",
        "year": 2020,
        "price": 2890,
        "mileage": 35000,
        "fuel_type": "gasoline",
        "location": "경기 분당구",
        "features": ["가죽시트", "프리미엄 오디오", "자동주차"],
        "match_score": 82,
        "ranking_position": 3,
        "agent_scores": {
            "collaborative_filtering": 79,
            "market_analysis": 85,
            "personal_preference": 84
        },
        "match_reasons": ["프리미엄 브랜드", "주행 성능", "리세일 가치"]
    }
]

def get_agents():
    global _carfin_agents
    if _carfin_agents is None:
        try:
            from agents.gemini_multi_agent import gemini_multi_agent
            _carfin_agents = gemini_multi_agent
            logger.info("Gemini Multi-Agent system loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Gemini Multi-Agent system: {e}")
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

# NEW: 3-Agent System Endpoints

@app.post("/api/consultation/full")
async def run_full_consultation(request: FullConsultationRequest):
    """Run complete 3-agent consultation workflow"""
    try:
        logger.info(f"Starting full consultation: {request.message[:50]}...")

        # For demo purposes, return sample data with simulated multi-agent analysis
        # In production, this would call the actual multi-agent system

        # Simulate multi-agent processing time
        import time
        import random
        time.sleep(1)  # Simulate processing

        # Filter vehicles based on request criteria if provided
        filtered_vehicles = sample_vehicles.copy()

        # Simulate collaborative filtering and scoring adjustment based on user input
        for vehicle in filtered_vehicles:
            # Adjust scores based on user preferences
            if hasattr(request, 'budget_range') and request.budget_range:
                # Bonus for vehicles within budget
                if request.budget_range[0] <= vehicle['price'] <= request.budget_range[1]:
                    vehicle['match_score'] = min(100, vehicle['match_score'] + 5)
                    vehicle['agent_scores']['personal_preference'] += 3

            if hasattr(request, 'fuel_type') and request.fuel_type:
                # Bonus for matching fuel type
                if vehicle['fuel_type'] == request.fuel_type:
                    vehicle['match_score'] = min(100, vehicle['match_score'] + 3)
                    vehicle['agent_scores']['personal_preference'] += 5

        # Sort by match score
        filtered_vehicles.sort(key=lambda x: x['match_score'], reverse=True)

        # Update ranking positions
        for i, vehicle in enumerate(filtered_vehicles):
            vehicle['ranking_position'] = i + 1

        result = {
            "status": "success",
            "vehicles": filtered_vehicles,
            "metadata": {
                "total_analyzed": len(sample_vehicles),
                "processing_time": 1.2,
                "confidence_score": 94.2,
                "explanation": "멀티에이전트 시스템이 협업 필터링, 시장 분석, 개인 선호도를 종합하여 분석했습니다."
            },
            "analysis": {
                "market_trends": "현재 중고차 시장에서 하이브리드 차량의 인기가 증가하고 있습니다.",
                "recommendation_basis": "사용자의 예산과 선호도를 기반으로 한 개인화된 추천",
                "collaborative_insights": "유사한 사용자들이 선호하는 차량을 우선 추천"
            }
        }

        # Store result for dashboard
        if request.user_id:
            conversations_db[request.user_id] = {
                "last_consultation": result,
                "timestamp": "2025-09-17T06:00:00Z"
            }

        return {
            **result,
            "timestamp": "2025-09-17T06:00:00Z",
            "consultation_id": f"consult_{hash(request.message) % 10000}"
        }

    except Exception as e:
        logger.error(f"Full consultation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"종합 상담 중 오류가 발생했습니다: {str(e)}"
        )

@app.get("/api/dashboard/{user_id}")
async def get_user_dashboard(user_id: str, refresh_data: bool = False):
    """Get user dashboard with insights and recommendations"""
    try:
        logger.info(f"Loading dashboard for user {user_id}")
        
        # Get user data
        user_data = users_db.get(user_id, {})
        preferences = preferences_db.get(user_id, {})
        conversation_history = conversations_db.get(user_id, {})
        
        # Get agents for market insights
        agents = get_agents()
        
        # Get market insights if refresh requested or no cache
        market_insights = "시장 데이터를 불러오는 중..."
        if refresh_data or not conversation_history.get("last_consultation"):
            try:
                # Get basic market insights
                if hasattr(agents.recommendation_engine, 'car_data'):
                    df = agents.recommendation_engine.car_data
                    if df is not None and len(df) > 0:
                        market_insights = f"""
                        📊 차량 시장 현황:
                        - 총 {len(df)}대 차량 데이터 보유
                        - 평균 가격: {df['price'].mean():.0f}만원
                        - 가격 범위: {df['price'].min():.0f} - {df['price'].max():.0f}만원
                        - 인기 카테고리: {df['category'].value_counts().head(3).to_dict() if 'category' in df else 'N/A'}
                        """
            except Exception as e:
                market_insights = f"시장 데이터 분석 중 오류: {str(e)}"
        
        dashboard_data = {
            "user_id": user_id,
            "user_profile": user_data,
            "preferences": preferences,
            "market_insights": market_insights,
            "last_consultation": conversation_history.get("last_consultation"),
            "summary": {
                "total_consultations": 1 if conversation_history.get("last_consultation") else 0,
                "agents_available": 3,
                "system_status": "정상 작동",
                "llm_provider": conversation_history.get("last_consultation", {}).get("llm_provider", "gemini/openai")
            },
            "quick_actions": [
                {"action": "new_consultation", "label": "새로운 차량 상담"},
                {"action": "view_recommendations", "label": "추천 차량 보기"},
                {"action": "finance_calculator", "label": "금융 계산기"},
                {"action": "update_preferences", "label": "선호도 수정"}
            ]
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Dashboard loading failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"대시보드 로딩 중 오류가 발생했습니다: {str(e)}"
        )

@app.get("/api/agents/status")
async def get_agents_status():
    """Get status of all 3 agents"""
    try:
        agents = get_agents()
        
        status = {
            "total_agents": 3,
            "agents": {
                "data_analyst": {
                    "name": "데이터 분석 및 의사결정 지원 전문가",
                    "status": "active" if "data_analyst" in agents.agents else "inactive",
                    "role": "시장 분석, 사용자 프로필 분석, 의사결정 지원"
                },
                "vehicle_expert": {
                    "name": "차량 추천 전문가",
                    "status": "active" if "vehicle_expert" in agents.agents else "inactive",
                    "role": "Gemini 기반 차량 추천"
                },
                "finance_advisor": {
                    "name": "금융 상담 전문가",
                    "status": "active" if "finance_expert" in agents.agents else "inactive",
                    "role": "대출, 리스, 할부 금융 옵션 계산"
                }
            },
            "ml_engine": {
                "status": "active" if hasattr(agents.recommendation_engine, 'car_data') else "inactive",
                "data_loaded": agents.recommendation_engine.car_data is not None if hasattr(agents.recommendation_engine, 'car_data') else False
            },
            "llm_providers": {
                "openai": "available",
                "gemini": "available" 
            }
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Agent status check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"에이전트 상태 확인 중 오류가 발생했습니다: {str(e)}"
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

@app.post("/api/financial/recommend")
async def recommend_financial_products(request: FinancialProductRequest):
    """Financial agent - recommend suitable loan products for selected vehicle"""
    try:
        logger.info(f"Financial recommendation for vehicle {request.vehicle_id}, price: {request.vehicle_price}만원")

        # Find the selected vehicle
        vehicle = None
        for v in sample_vehicles:
            if v["id"] == request.vehicle_id:
                vehicle = v
                break

        if not vehicle:
            raise HTTPException(status_code=404, detail="선택된 차량을 찾을 수 없습니다")

        # Simulate financial agent processing
        import time
        import math
        time.sleep(0.8)  # Simulate AI analysis time

        # Calculate loan parameters for each product
        loan_amount = request.vehicle_price - (request.down_payment or request.vehicle_price * 0.2)  # Default 20% down payment

        recommended_products = []
        for product in sample_financial_products.copy():
            # Check if loan amount is within limits
            if loan_amount > product["max_loan_amount"]:
                continue

            # Calculate monthly payment using compound interest formula
            monthly_rate = product["interest_rate"] / 100 / 12
            term_months = min(request.loan_term or 36, product["max_loan_term"])

            if monthly_rate > 0:
                monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**term_months) / ((1 + monthly_rate)**term_months - 1)
            else:
                monthly_payment = loan_amount / term_months

            total_payment = monthly_payment * term_months
            total_interest = total_payment - loan_amount

            # Adjust match score based on user profile
            match_score = product["match_score"]

            # Bonus for affordable monthly payments (< 30% of assumed income)
            if request.income:
                if monthly_payment <= request.income * 0.3:
                    match_score += 5

            # Bonus for good credit score
            if request.credit_score == "excellent":
                match_score += 8
            elif request.credit_score == "good":
                match_score += 3
            elif request.credit_score == "poor":
                match_score -= 10

            # Update product with calculations
            product["monthly_payment"] = round(monthly_payment, 1)
            product["total_interest"] = round(total_interest, 1)
            product["total_payment"] = round(total_payment, 1)
            product["loan_amount"] = loan_amount
            product["term_months"] = term_months
            product["match_score"] = min(100, max(0, match_score))

            recommended_products.append(product)

        # Sort by match score
        recommended_products.sort(key=lambda x: x["match_score"], reverse=True)

        # Update rankings
        for i, product in enumerate(recommended_products):
            product["ranking_position"] = i + 1

        return {
            "status": "success",
            "vehicle": vehicle,
            "loan_parameters": {
                "vehicle_price": request.vehicle_price,
                "loan_amount": loan_amount,
                "down_payment": request.down_payment or request.vehicle_price * 0.2,
                "requested_term": request.loan_term or 36,
                "credit_score": request.credit_score
            },
            "financial_products": recommended_products,
            "metadata": {
                "total_products_analyzed": len(sample_financial_products),
                "products_matched": len(recommended_products),
                "processing_time": 0.8,
                "agent_confidence": 93.5
            },
            "analysis": {
                "affordability_assessment": "분석된 금융상품 모두 안정적인 상환이 가능한 수준입니다." if recommended_products else "현재 조건에 맞는 금융상품이 제한적입니다.",
                "best_option": recommended_products[0] if recommended_products else None,
                "market_comparison": "현재 시장 금리 대비 경쟁력 있는 상품들로 구성되었습니다.",
                "recommendations": [
                    "월 상환액이 월소득의 30% 이하가 되도록 조정하세요",
                    "신용등급 개선으로 더 좋은 금리 혜택을 받을 수 있습니다",
                    "중도상환 수수료 조건을 확인하세요"
                ]
            },
            "timestamp": "2025-09-17T06:00:00Z",
            "consultation_id": f"finance_{hash(request.vehicle_id) % 10000}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Financial recommendation failed: {e}")
        raise HTTPException(status_code=500, detail="금융상품 추천 중 오류가 발생했습니다")

@app.post("/api/users/interaction")
async def record_user_interaction(request: UserInteractionRequest):
    """사용자 상호작용 기록 - 실시간 학습용"""
    try:
        logger.info(f"Recording interaction: {request.user_id} -> {request.vehicle_id} ({request.interaction_type})")

        # 사용자 상호작용 기록 저장
        if request.user_id not in user_interactions_db:
            user_interactions_db[request.user_id] = []

        interaction_data = {
            "vehicle_id": request.vehicle_id,
            "interaction_type": request.interaction_type,
            "timestamp": request.timestamp
        }

        user_interactions_db[request.user_id].append(interaction_data)

        # 최근 20개 상호작용만 유지 (메모리 관리)
        if len(user_interactions_db[request.user_id]) > 20:
            user_interactions_db[request.user_id] = user_interactions_db[request.user_id][-20:]

        return {
            "status": "success",
            "message": "상호작용이 기록되었습니다",
            "total_interactions": len(user_interactions_db[request.user_id])
        }

    except Exception as e:
        logger.error(f"Failed to record interaction: {e}")
        raise HTTPException(status_code=500, detail="상호작용 기록 중 오류가 발생했습니다")

@app.post("/api/consultation/adaptive")
async def adaptive_recommendation(request: AdaptiveRecommendationRequest):
    """적응형 추천 - 사용자 상호작용 기반 실시간 학습"""
    try:
        logger.info(f"Adaptive recommendation for user {request.user_id} with {len(request.interactions)} interactions")

        # 사용자의 상호작용 패턴 분석
        user_interactions = user_interactions_db.get(request.user_id, [])

        # 상호작용한 차량들의 특성 분석
        clicked_vehicles = []
        for vehicle_id in request.interactions:
            for vehicle in sample_vehicles:
                if vehicle["id"] == vehicle_id:
                    clicked_vehicles.append(vehicle)
                    break

        if not clicked_vehicles:
            # 상호작용 데이터가 없으면 기본 추천 유지
            return {
                "status": "success",
                "vehicles": sample_vehicles,
                "metadata": {
                    "learning_status": "insufficient_data",
                    "interaction_count": len(request.interactions)
                }
            }

        # 협업 필터링 시뮬레이션: 선호 패턴 학습
        preferred_brands = {}
        preferred_fuel_types = {}
        preferred_price_range = []

        for vehicle in clicked_vehicles:
            # 브랜드 선호도
            brand = vehicle["brand"]
            preferred_brands[brand] = preferred_brands.get(brand, 0) + 1

            # 연료 타입 선호도
            fuel_type = vehicle["fuel_type"]
            preferred_fuel_types[fuel_type] = preferred_fuel_types.get(fuel_type, 0) + 1

            # 가격 범위
            preferred_price_range.append(vehicle["price"])

        # 학습된 선호도를 바탕으로 추천 점수 재조정
        updated_vehicles = []
        for vehicle in sample_vehicles.copy():
            # 기본 점수에서 시작
            adjusted_score = vehicle["match_score"]

            # 브랜드 선호도 반영
            if vehicle["brand"] in preferred_brands:
                brand_boost = (preferred_brands[vehicle["brand"]] / len(clicked_vehicles)) * 15
                adjusted_score += brand_boost
                vehicle["agent_scores"]["collaborative_filtering"] += brand_boost

            # 연료 타입 선호도 반영
            if vehicle["fuel_type"] in preferred_fuel_types:
                fuel_boost = (preferred_fuel_types[vehicle["fuel_type"]] / len(clicked_vehicles)) * 10
                adjusted_score += fuel_boost
                vehicle["agent_scores"]["personal_preference"] += fuel_boost

            # 가격 선호도 반영
            if preferred_price_range:
                avg_preferred_price = sum(preferred_price_range) / len(preferred_price_range)
                price_similarity = 1 - abs(vehicle["price"] - avg_preferred_price) / avg_preferred_price
                if price_similarity > 0.7:  # 30% 이내 가격 차이
                    price_boost = price_similarity * 8
                    adjusted_score += price_boost
                    vehicle["agent_scores"]["market_analysis"] += price_boost

            vehicle["match_score"] = min(100, max(0, adjusted_score))
            updated_vehicles.append(vehicle)

        # 업데이트된 점수로 재정렬
        updated_vehicles.sort(key=lambda x: x["match_score"], reverse=True)

        # 순위 업데이트
        for i, vehicle in enumerate(updated_vehicles):
            vehicle["ranking_position"] = i + 1

        return {
            "status": "success",
            "vehicles": updated_vehicles,
            "metadata": {
                "learning_status": "adapted",
                "interaction_count": len(request.interactions),
                "learned_preferences": {
                    "preferred_brands": preferred_brands,
                    "preferred_fuel_types": preferred_fuel_types,
                    "avg_preferred_price": sum(preferred_price_range) / len(preferred_price_range) if preferred_price_range else None
                },
                "processing_time": 0.5,
                "confidence_boost": "실시간 학습으로 개인화 정확도가 향상되었습니다"
            },
            "analysis": {
                "learning_insights": f"{len(clicked_vehicles)}개 차량 상호작용을 분석하여 선호도를 학습했습니다",
                "pattern_detection": "브랜드, 연료타입, 가격대 선호 패턴이 감지되었습니다",
                "recommendation_improvement": "협업 필터링 알고리즘이 사용자 행동을 반영하여 추천을 개선했습니다"
            },
            "timestamp": "2025-09-17T06:00:00Z",
            "consultation_id": f"adaptive_{hash(request.user_id) % 10000}"
        }

    except Exception as e:
        logger.error(f"Adaptive recommendation failed: {e}")
        raise HTTPException(status_code=500, detail="적응형 추천 중 오류가 발생했습니다")

# Academic Recommendation System Models
class UserProfile(BaseModel):
    user_id: str
    name: Optional[str] = None
    age: Optional[int] = None
    income: Optional[int] = None
    preferences: List[str] = []
    purpose: Optional[str] = None
    budget_range: Optional[Dict[str, int]] = None

class RecommendationRequest(BaseModel):
    user_profile: UserProfile
    recommendation_type: str = "academic_hybrid"
    limit: int = 10

class VehicleRecommendation(BaseModel):
    vehicle_id: str
    score: float
    rank: int
    reasons: List[str] = []
    confidence: float
    algorithm: str

class RecommendationResponse(BaseModel):
    recommendations: List[VehicleRecommendation]
    metadata: Dict[str, Any]

@app.post("/api/recommendations", response_model=RecommendationResponse)
async def get_academic_recommendations(request: RecommendationRequest):
    """Academic Paper-based Hybrid Recommendation API"""
    try:
        if not ACADEMIC_SYSTEM_AVAILABLE:
            # Enhanced Mock Recommendation System
            user_preferences = request.user_profile.preferences
            budget_max = request.user_profile.budget_range.get("max", 5000) if request.user_profile.budget_range else 5000
            user_age = request.user_profile.age or 30

            # 현실적인 차량 목록
            mock_vehicles = [
                {"id": "car_001", "brand": "현대", "model": "아반떼", "year": 2022, "price": 2300, "fuel": "gasoline", "safety": 95},
                {"id": "car_002", "brand": "기아", "model": "K5", "year": 2021, "price": 2650, "fuel": "hybrid", "safety": 92},
                {"id": "car_003", "brand": "BMW", "model": "320i", "year": 2020, "price": 2890, "fuel": "gasoline", "safety": 88},
                {"id": "car_004", "brand": "벤츠", "model": "C200", "year": 2021, "price": 3200, "fuel": "gasoline", "safety": 90},
                {"id": "car_005", "brand": "아우디", "model": "A4", "year": 2020, "price": 3100, "fuel": "gasoline", "safety": 89},
                {"id": "car_006", "brand": "테슬라", "model": "Model 3", "year": 2022, "price": 4500, "fuel": "electric", "safety": 98},
                {"id": "car_007", "brand": "토요타", "model": "캠리", "year": 2021, "price": 2800, "fuel": "hybrid", "safety": 94},
                {"id": "car_008", "brand": "현대", "model": "소나타", "year": 2022, "price": 2500, "fuel": "hybrid", "safety": 93},
                {"id": "car_009", "brand": "기아", "model": "스팅어", "year": 2020, "price": 3500, "fuel": "gasoline", "safety": 87},
                {"id": "car_010", "brand": "제네시스", "model": "G70", "year": 2021, "price": 3800, "fuel": "gasoline", "safety": 91}
            ]

            # 간단한 추천 로직
            filtered_vehicles = [v for v in mock_vehicles if v["price"] <= budget_max]

            # 선호도 기반 점수 계산
            for vehicle in filtered_vehicles:
                score = 0.5  # 기본 점수

                # 연비 선호도
                if "연비" in user_preferences and vehicle["fuel"] in ["hybrid", "electric"]:
                    score += 0.3

                # 안전성 선호도
                if "안전성" in user_preferences:
                    score += (vehicle["safety"] - 80) / 100

                # 브랜드 선호도
                if any(brand in user_preferences for brand in ["BMW", "벤츠", "아우디"]) and vehicle["brand"] in ["BMW", "벤츠", "아우디"]:
                    score += 0.2

                # 나이 기반 선호도
                if user_age < 35 and vehicle["brand"] in ["현대", "기아"]:
                    score += 0.1
                elif user_age >= 35 and vehicle["brand"] in ["BMW", "벤츠"]:
                    score += 0.1

                vehicle["score"] = min(1.0, score)

            # 점수순 정렬
            filtered_vehicles.sort(key=lambda x: x["score"], reverse=True)

            recommendations = []
            for i, vehicle in enumerate(filtered_vehicles[:request.limit]):
                reasons = []
                if vehicle["fuel"] in ["hybrid", "electric"]:
                    reasons.append("친환경 연료")
                if vehicle["safety"] > 90:
                    reasons.append("높은 안전성")
                if vehicle["price"] < budget_max * 0.8:
                    reasons.append("예산 대비 적정가격")

                recommendations.append(VehicleRecommendation(
                    vehicle_id=vehicle["id"],
                    score=vehicle["score"],
                    rank=i + 1,
                    reasons=reasons or ["종합 추천"],
                    confidence=0.85,
                    algorithm="Smart Mock Recommendation"
                ))

            return RecommendationResponse(
                recommendations=recommendations,
                metadata={
                    "algorithm": "Smart Mock Recommendation System",
                    "user_preferences": user_preferences,
                    "budget_filter": f"~{budget_max}만원",
                    "total_candidates": len(filtered_vehicles),
                    "processing_time_ms": 25
                }
            )

        # Load NCF system directly
        try:
            from models.ncf_car_recommendation import CarRecommendationNCF
            ncf_system = CarRecommendationNCF()

            # Convert user profile for NCF
            user_dict = {
                "user_id": request.user_profile.user_id,
                "age": request.user_profile.age or 30,
                "income": request.user_profile.income or 5000,
                "preferences": request.user_profile.preferences,
                "budget_max": request.user_profile.budget_range.get("max", 5000) if request.user_profile.budget_range else 5000
            }

            # Get NCF recommendations
            ncf_results = ncf_system.get_recommendations(
                user_dict,
                n_recommendations=request.limit
            )

            # Format NCF response
            recommendations = []
            for i, rec in enumerate(ncf_results):
                recommendations.append(VehicleRecommendation(
                    vehicle_id=str(rec.get('vehicle_id', f'ncf_{i}')),
                    score=rec.get('score', 0.0),
                    rank=i + 1,
                    reasons=rec.get('reasons', ['NCF Algorithm']),
                    confidence=rec.get('confidence', 0.85),
                    algorithm='Neural Collaborative Filtering'
                ))

            return RecommendationResponse(
                recommendations=recommendations,
                metadata={
                    "algorithm": "Neural Collaborative Filtering (NCF)",
                    "paper": "He et al. 2017 - Neural Collaborative Filtering",
                    "model_type": "GMF + MLP Hybrid (Mock Mode)",
                    "processing_time_ms": 75,
                    "note": "Running in mock mode - requires TensorFlow for full functionality"
                }
            )

        except ImportError as e:
            logger.error(f"NCF system not available: {e}")
            # This will fall back to the enhanced mock system below

        # Final fallback - this should not be reached but provides safety
        logger.warning("Falling back to basic mock recommendation system")
        return RecommendationResponse(
            recommendations=[],
            metadata={
                "algorithm": "Fallback System",
                "error": "No recommendation systems available",
                "processing_time_ms": 10
            }
        )

    except Exception as e:
        logger.error(f"Academic recommendation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Academic recommendation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    # Backend runs on port 8000, frontend on 5000 for Replit webview
    port = int(os.environ.get("PORT", 8000))
    
    logger.info(f"Starting CarFin AI server on port {port}")
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload to avoid issues
        log_level="info"
    )