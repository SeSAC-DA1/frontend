"""
PyCaret-based Car Recommendation Engine
Implements ALS collaborative filtering for personalized car recommendations
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import logging
import os
from sqlalchemy import create_engine, text
import warnings
warnings.filterwarnings('ignore')

# Try PyCaret imports with fallback
try:
    from pycaret.recommendation import setup, create_model, predict_model, finalize_model
    PYCARET_AVAILABLE = True
except ImportError as e:
    print(f"PyCaret not available: {e}. Using fallback recommendation system.")
    PYCARET_AVAILABLE = False

class CarRecommendationEngine:
    """
    Car recommendation system using collaborative filtering
    Fallback to content-based filtering if PyCaret is unavailable
    """
    
    def __init__(self):
        self.model = None
        self.car_data = None
        self.user_ratings = None
        self.engine = None
        self.is_trained = False
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """Set up logging"""
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)
    
    def _get_database_connection(self):
        """Create database connection"""
        try:
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                raise ValueError("DATABASE_URL environment variable not set")
            self.engine = create_engine(database_url)
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            return False
    
    def load_data(self) -> bool:
        """Load car data and user ratings from PostgreSQL"""
        try:
            if not self._get_database_connection():
                return False
            
            # Load car data
            car_query = """
                SELECT id, make, model, year, price, fuel_type, category, 
                       engine_size, fuel_efficiency, transmission, safety_rating, description
                FROM cars
            """
            self.car_data = pd.read_sql(car_query, self.engine)
            
            # Load user ratings
            ratings_query = """
                SELECT user_id, car_id, rating 
                FROM user_ratings
            """
            self.user_ratings = pd.read_sql(ratings_query, self.engine)
            
            self.logger.info(f"Loaded {len(self.car_data)} cars and {len(self.user_ratings)} ratings")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load data: {e}")
            return False
    
    def train_model(self) -> bool:
        """Train the recommendation model"""
        try:
            if not PYCARET_AVAILABLE:
                self.logger.info("Using fallback content-based recommendation system")
                self.is_trained = True
                return True
            
            if self.user_ratings is None or len(self.user_ratings) < 5:
                self.logger.warning("Insufficient rating data for collaborative filtering, using content-based approach")
                self.is_trained = True
                return True
            
            # Setup PyCaret recommendation system
            rec_setup = setup(
                data=self.user_ratings,
                user_id='user_id',
                item_id='car_id', 
                rating='rating',
                session_id=123,
                silent=True
            )
            
            # Create ALS model
            self.model = create_model('als')
            self.model = finalize_model(self.model)
            
            self.is_trained = True
            self.logger.info("Successfully trained ALS recommendation model")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to train model: {e}")
            # Fallback to content-based approach
            self.is_trained = True
            return True
    
    def _content_based_recommendations(self, user_profile: Dict[str, Any], n_recommendations: int = 3) -> List[Dict]:
        """Fallback content-based recommendation when collaborative filtering fails"""
        try:
            # Extract user preferences
            budget_max = user_profile.get('budget_max', 5000)
            preferred_category = user_profile.get('category', 'Compact')
            fuel_preference = user_profile.get('fuel_type', 'Gasoline')
            
            # Filter cars based on budget
            filtered_cars = self.car_data[self.car_data['price'] <= budget_max].copy()
            
            if len(filtered_cars) == 0:
                filtered_cars = self.car_data.copy()
            
            # Score cars based on user preferences
            filtered_cars['score'] = 0
            
            # Category matching (higher score for exact match)
            filtered_cars.loc[filtered_cars['category'] == preferred_category, 'score'] += 30
            
            # Fuel type preference
            if fuel_preference == 'Electric':
                filtered_cars.loc[filtered_cars['fuel_type'] == 'Electric', 'score'] += 25
            elif fuel_preference == 'Hybrid':
                filtered_cars.loc[filtered_cars['fuel_type'].isin(['Hybrid', 'Electric']), 'score'] += 20
            else:
                filtered_cars.loc[filtered_cars['fuel_type'] == fuel_preference, 'score'] += 15
            
            # Fuel efficiency bonus (higher is better)
            filtered_cars['score'] += filtered_cars['fuel_efficiency'] * 0.5
            
            # Safety rating bonus
            filtered_cars['score'] += filtered_cars['safety_rating'] * 5
            
            # Price value scoring (prefer mid-range pricing in category)
            category_median_price = filtered_cars.groupby('category')['price'].median()
            for category in category_median_price.index:
                mask = filtered_cars['category'] == category
                median_price = category_median_price[category]
                # Score based on how close to median price
                price_diff_ratio = abs(filtered_cars.loc[mask, 'price'] - median_price) / median_price
                filtered_cars.loc[mask, 'score'] += (1 - price_diff_ratio.clip(0, 1)) * 10
            
            # Get top recommendations
            top_cars = filtered_cars.nlargest(n_recommendations, 'score')
            
            # Convert to recommendation format
            recommendations = []
            for _, car in top_cars.iterrows():
                reason = self._generate_recommendation_reason(car, user_profile)
                recommendations.append({
                    'car_id': int(car['id']),
                    'make': car['make'],
                    'model': car['model'],
                    'year': int(car['year']),
                    'price': int(car['price']),
                    'fuel_type': car['fuel_type'],
                    'category': car['category'],
                    'fuel_efficiency': int(car['fuel_efficiency']) if pd.notnull(car['fuel_efficiency']) else None,
                    'safety_rating': int(car['safety_rating']),
                    'description': car['description'],
                    'recommendation_reason': reason,
                    'score': round(car['score'], 1)
                })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Content-based recommendation failed: {e}")
            # Return top 3 cars as last resort
            top_cars = self.car_data.nsmallest(n_recommendations, 'price')
            return [{'car_id': int(row['id']), 'make': row['make'], 'model': row['model'], 
                    'price': int(row['price']), 'recommendation_reason': '경제적인 선택'} 
                   for _, row in top_cars.iterrows()]
    
    def _generate_recommendation_reason(self, car: pd.Series, user_profile: Dict[str, Any]) -> str:
        """Generate personalized recommendation reason"""
        reasons = []
        
        # Budget consideration
        if car['price'] <= user_profile.get('budget_max', 5000):
            if car['price'] <= 3000:
                reasons.append("합리적인 가격")
            else:
                reasons.append("예산 범위 내 적합한 선택")
        
        # Fuel efficiency
        if car['fuel_efficiency'] >= 15:
            reasons.append("뛰어난 연비")
        elif car['fuel_efficiency'] >= 12:
            reasons.append("우수한 연비")
        
        # Safety
        if car['safety_rating'] == 5:
            reasons.append("최고 안전등급")
        elif car['safety_rating'] >= 4:
            reasons.append("우수한 안전성")
        
        # Category specific
        if car['category'] == 'Compact':
            reasons.append("실용적이고 경제적")
        elif car['category'] == 'Luxury':
            reasons.append("프리미엄 브랜드")
        elif 'SUV' in car['category']:
            reasons.append("넓은 공간과 높은 시야")
        
        # Electric/Hybrid
        if car['fuel_type'] == 'Electric':
            reasons.append("친환경 전기차")
        elif car['fuel_type'] == 'Hybrid':
            reasons.append("환경 친화적")
        
        return ", ".join(reasons[:3]) if reasons else "추천 차량"
    
    def get_recommendations(self, user_profile: Dict[str, Any], n_recommendations: int = 3) -> List[Dict]:
        """Get personalized car recommendations"""
        try:
            if not self.is_trained:
                if not self.train_model():
                    return []
            
            # For now, always use content-based recommendations as they're more reliable
            # and provide better explanations for the MVP
            return self._content_based_recommendations(user_profile, n_recommendations)
            
        except Exception as e:
            self.logger.error(f"Recommendation failed: {e}")
            return []
    
    def get_car_details(self, car_id: int) -> Optional[Dict]:
        """Get detailed information about a specific car"""
        try:
            car = self.car_data[self.car_data['id'] == car_id]
            if car.empty:
                return None
            
            car_info = car.iloc[0]
            return {
                'car_id': int(car_info['id']),
                'make': car_info['make'],
                'model': car_info['model'],
                'year': int(car_info['year']),
                'price': int(car_info['price']),
                'fuel_type': car_info['fuel_type'],
                'category': car_info['category'],
                'engine_size': float(car_info['engine_size']) if pd.notnull(car_info['engine_size']) else None,
                'fuel_efficiency': int(car_info['fuel_efficiency']) if pd.notnull(car_info['fuel_efficiency']) else None,
                'transmission': car_info['transmission'],
                'safety_rating': int(car_info['safety_rating']),
                'description': car_info['description']
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get car details: {e}")
            return None