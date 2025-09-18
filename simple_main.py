"""
CarFin AI FastAPI Backend - Simplified with NCF Integration
"""
import os
import sys
import logging
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CarFin AI",
    description="NCF-based Car Recommendation System",
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

# Pydantic models for NCF integration
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
    recommendation_type: str = "ncf_hybrid"
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

# Global NCF model instance
ncf_model = None

def load_ncf_model():
    """NCF 모델 로드"""
    global ncf_model
    try:
        # Add models path
        sys.path.append(os.path.join(os.path.dirname(__file__), 'models'))

        from real_ncf_engine import RealNCFEngine
        ncf_model = RealNCFEngine()
        logger.info("✅ NCF 모델 로드 성공")
        return True
    except Exception as e:
        logger.warning(f"⚠️ NCF 모델 로드 실패: {e}")
        ncf_model = None
        return False

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "CarFin AI Backend is running",
        "status": "healthy",
        "version": "1.0.0",
        "ncf_model": "loaded" if ncf_model else "not loaded"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    ncf_status = "available" if ncf_model else "unavailable"

    return {
        "status": "healthy",
        "ncf_model": ncf_status,
        "recommendation_engine": "ready"
    }

@app.post("/api/recommendations", response_model=RecommendationResponse)
async def get_ncf_recommendations(request: RecommendationRequest):
    """NCF 기반 차량 추천 API"""
    try:
        logger.info(f"NCF 추천 요청: 사용자 {request.user_profile.user_id}")

        # NCF 모델이 로드되지 않았으면 로드 시도
        if ncf_model is None:
            load_ncf_model()

        # NCF 모델 사용 또는 Mock 시스템
        if ncf_model is not None:
            # NCF 모델을 통한 추천
            user_dict = {
                "user_id": request.user_profile.user_id,
                "age": request.user_profile.age or 30,
                "income": request.user_profile.income or 5000,
                "preferences": request.user_profile.preferences,
                "budget_max": request.user_profile.budget_range.get("max", 5000) if request.user_profile.budget_range else 5000
            }

            ncf_results = ncf_model.get_recommendations(
                user_dict,
                n_recommendations=request.limit
            )

            # NCF 결과를 API 형식으로 변환
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
                    "model_type": "GMF + MLP Hybrid",
                    "mode": "ncf_mock" if not hasattr(ncf_model, 'model') or ncf_model.model is None else "ncf_trained",
                    "processing_time_ms": 75,
                    "user_preferences": request.user_profile.preferences
                }
            )

        else:
            # Enhanced Mock 추천 시스템 (NCF 없을 때)
            user_preferences = request.user_profile.preferences
            budget_max = request.user_profile.budget_range.get("max", 5000) if request.user_profile.budget_range else 5000
            user_age = request.user_profile.age or 30

            # 현실적인 차량 데이터
            mock_vehicles = [
                {"id": "car_001", "brand": "현대", "model": "아반떼", "year": 2022, "price": 2300, "fuel": "gasoline", "safety": 95},
                {"id": "car_002", "brand": "기아", "model": "K5", "year": 2021, "price": 2650, "fuel": "hybrid", "safety": 92},
                {"id": "car_003", "brand": "BMW", "model": "320i", "year": 2020, "price": 2890, "fuel": "gasoline", "safety": 88},
                {"id": "car_004", "brand": "벤츠", "model": "C200", "year": 2021, "price": 3200, "fuel": "gasoline", "safety": 90},
                {"id": "car_005", "brand": "아우디", "model": "A4", "year": 2020, "price": 3100, "fuel": "gasoline", "safety": 89},
                {"id": "car_006", "brand": "테슬라", "model": "Model 3", "year": 2022, "price": 4500, "fuel": "electric", "safety": 98},
                {"id": "car_007", "brand": "토요타", "model": "캠리", "year": 2021, "price": 2800, "fuel": "hybrid", "safety": 94},
                {"id": "car_008", "brand": "현대", "model": "소나타", "year": 2022, "price": 2500, "fuel": "hybrid", "safety": 93},
            ]

            # 예산 내 차량 필터링
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
                    confidence=0.82,
                    algorithm="Enhanced Mock Recommendation"
                ))

            return RecommendationResponse(
                recommendations=recommendations,
                metadata={
                    "algorithm": "Enhanced Mock Recommendation System",
                    "mode": "fallback",
                    "user_preferences": user_preferences,
                    "budget_filter": f"~{budget_max}만원",
                    "total_candidates": len(filtered_vehicles),
                    "processing_time_ms": 25,
                    "note": "NCF 모델 로드 실패 - Mock 시스템 사용"
                }
            )

    except Exception as e:
        logger.error(f"추천 시스템 오류: {e}")
        raise HTTPException(status_code=500, detail=f"추천 시스템 오류: {str(e)}")

# 애플리케이션 시작 시 NCF 모델 로드 시도
@app.on_event("startup")
async def startup_event():
    """서버 시작 시 NCF 모델 로드"""
    logger.info("🚀 CarFin AI Backend 시작")
    load_ncf_model()

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting CarFin AI server on port {port}")

    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )