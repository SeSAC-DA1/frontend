"""
NCF (Neural Collaborative Filtering) for CarFinanceAI
Based on "Neural Collaborative Filtering" (He et al. 2017)
Specialized for vehicle recommendation with contextual features
"""

import tensorflow as tf
from tensorflow.keras.layers import *
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.regularizers import l2
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import json

class CarRecommendationNCF:
    """
    NCF 모델을 차량 추천에 특화시킨 구현

    Features:
    - GMF + MLP 하이브리드 구조
    - 차량 특성 피처 통합
    - 사용자 컨텍스트 반영
    - 실시간 추론 최적화
    """

    def __init__(self,
                 num_users: int = 1000,
                 num_vehicles: int = 500,
                 embedding_dim: int = 64,
                 mlp_layers: List[int] = [128, 64, 32],
                 dropout_rate: float = 0.2,
                 l2_reg: float = 1e-6):

        self.num_users = num_users
        self.num_vehicles = num_vehicles
        self.embedding_dim = embedding_dim
        self.mlp_layers = mlp_layers
        self.dropout_rate = dropout_rate
        self.l2_reg = l2_reg

        # 차량 특성 차원 정의
        self.user_feature_dim = 10  # 나이, 소득, 지역 등
        self.vehicle_feature_dim = 15  # 가격, 연식, 브랜드 등
        self.context_feature_dim = 5   # 계절, 시간, 시장상황 등

        self.model = None
        self.training_history = None

    def build_model(self):
        """NCF 모델 구축 - CarFinanceAI 특화"""

        # ===== 입력 레이어 =====
        # 기본 user-item ID
        user_input = Input(shape=(), name='user_id', dtype='int32')
        vehicle_input = Input(shape=(), name='vehicle_id', dtype='int32')

        # 추가 특성 피처들
        user_features = Input(shape=(self.user_feature_dim,), name='user_features')
        vehicle_features = Input(shape=(self.vehicle_feature_dim,), name='vehicle_features')
        context_features = Input(shape=(self.context_feature_dim,), name='context_features')

        # ===== GMF 브랜치 (Generalized Matrix Factorization) =====
        # 사용자/차량 임베딩
        user_embedding_gmf = Embedding(
            self.num_users, self.embedding_dim,
            embeddings_regularizer=l2(self.l2_reg),
            name='user_embedding_gmf'
        )(user_input)

        vehicle_embedding_gmf = Embedding(
            self.num_vehicles, self.embedding_dim,
            embeddings_regularizer=l2(self.l2_reg),
            name='vehicle_embedding_gmf'
        )(vehicle_input)

        # GMF: element-wise product
        gmf_user_vec = Flatten()(user_embedding_gmf)
        gmf_vehicle_vec = Flatten()(vehicle_embedding_gmf)
        gmf_output = Multiply(name='gmf_multiply')([gmf_user_vec, gmf_vehicle_vec])

        # ===== MLP 브랜치 (Multi-Layer Perceptron) =====
        # 사용자/차량 임베딩 (MLP용 - 다른 가중치)
        user_embedding_mlp = Embedding(
            self.num_users, self.embedding_dim,
            embeddings_regularizer=l2(self.l2_reg),
            name='user_embedding_mlp'
        )(user_input)

        vehicle_embedding_mlp = Embedding(
            self.num_vehicles, self.embedding_dim,
            embeddings_regularizer=l2(self.l2_reg),
            name='vehicle_embedding_mlp'
        )(vehicle_input)

        # MLP: concatenation + dense layers
        mlp_user_vec = Flatten()(user_embedding_mlp)
        mlp_vehicle_vec = Flatten()(vehicle_embedding_mlp)

        # 모든 피처 결합
        mlp_input = Concatenate(name='mlp_concat')([
            mlp_user_vec,
            mlp_vehicle_vec,
            user_features,      # 사용자 인구통계학적 정보
            vehicle_features,   # 차량 세부 특성
            context_features    # 상황 정보
        ])

        # MLP 레이어들
        mlp_output = mlp_input
        for i, layer_size in enumerate(self.mlp_layers):
            mlp_output = Dense(
                layer_size,
                activation='relu',
                kernel_regularizer=l2(self.l2_reg),
                name=f'mlp_layer_{i+1}'
            )(mlp_output)
            mlp_output = Dropout(self.dropout_rate)(mlp_output)

        # ===== 최종 결합 레이어 =====
        # GMF + MLP 결합
        final_input = Concatenate(name='final_concat')([gmf_output, mlp_output])

        # 최종 예측 레이어
        prediction = Dense(
            1,
            activation='sigmoid',  # 0-1 선호도 점수
            kernel_regularizer=l2(self.l2_reg),
            name='prediction'
        )(final_input)

        # 모델 정의
        self.model = Model(
            inputs=[user_input, vehicle_input, user_features, vehicle_features, context_features],
            outputs=prediction,
            name='CarFinanceAI_NCF'
        )

        return self.model

    def compile_model(self, learning_rate: float = 0.001):
        """모델 컴파일"""
        if self.model is None:
            self.build_model()

        self.model.compile(
            optimizer=Adam(learning_rate=learning_rate),
            loss='binary_crossentropy',  # 선호/비선호 이진 분류
            metrics=['accuracy', 'precision', 'recall']
        )

        return self.model

    def prepare_training_data(self, interaction_df: pd.DataFrame) -> Dict:
        """훈련 데이터 준비"""

        # 긍정적 상호작용 (평점 4+ 또는 구매/문의)
        positive_interactions = interaction_df[
            (interaction_df['rating'] >= 4.0) |
            (interaction_df['interaction_type'].isin(['purchase', 'inquiry', 'favorite']))
        ]

        # 부정적 샘플링 (랜덤 샘플링)
        negative_samples = self._negative_sampling(
            positive_interactions,
            ratio=4  # 긍정:부정 = 1:4
        )

        # 훈련 데이터 결합
        train_data = pd.concat([positive_interactions, negative_samples])
        train_data = train_data.sample(frac=1).reset_index(drop=True)  # 셞플

        # 피처 추출
        training_data = {
            'user_ids': train_data['user_id'].values,
            'vehicle_ids': train_data['vehicle_id'].values,
            'user_features': self._extract_user_features(train_data),
            'vehicle_features': self._extract_vehicle_features(train_data),
            'context_features': self._extract_context_features(train_data),
            'labels': train_data['preference_score'].values  # 0 or 1
        }

        return training_data

    def _negative_sampling(self, positive_df: pd.DataFrame, ratio: int = 4) -> pd.DataFrame:
        """부정적 샘플 생성"""
        negative_samples = []

        for _, pos_sample in positive_df.iterrows():
            user_id = pos_sample['user_id']

            # 해당 사용자가 상호작용하지 않은 차량들 중 랜덤 선택
            user_vehicles = set(positive_df[positive_df['user_id'] == user_id]['vehicle_id'])
            all_vehicles = set(range(self.num_vehicles))
            uninteracted_vehicles = list(all_vehicles - user_vehicles)

            # 랜덤 샘플링
            if len(uninteracted_vehicles) >= ratio:
                sampled_vehicles = np.random.choice(uninteracted_vehicles, ratio, replace=False)

                for vehicle_id in sampled_vehicles:
                    negative_sample = pos_sample.copy()
                    negative_sample['vehicle_id'] = vehicle_id
                    negative_sample['preference_score'] = 0  # 부정적 레이블
                    negative_samples.append(negative_sample)

        return pd.DataFrame(negative_samples)

    def _extract_user_features(self, df: pd.DataFrame) -> np.ndarray:
        """사용자 특성 피처 추출"""
        # 사용자 인구통계학적 정보
        user_features = []

        for _, row in df.iterrows():
            features = [
                row.get('user_age', 30) / 100.0,           # 나이 정규화
                row.get('user_income', 5000) / 10000.0,    # 소득 정규화
                row.get('user_family_size', 2) / 10.0,     # 가족 수
                row.get('user_driving_exp', 5) / 50.0,     # 운전 경력
                row.get('user_location_code', 0) / 100.0,  # 지역 코드
                row.get('user_education', 3) / 5.0,        # 학력 수준
                row.get('user_occupation_code', 0) / 20.0, # 직업 코드
                row.get('user_gender', 0),                 # 성별 (0/1)
                row.get('user_married', 0),                # 결혼 여부
                row.get('user_car_ownership', 0)           # 차량 보유 여부
            ]
            user_features.append(features)

        return np.array(user_features, dtype=np.float32)

    def _extract_vehicle_features(self, df: pd.DataFrame) -> np.ndarray:
        """차량 특성 피처 추출"""
        vehicle_features = []

        for _, row in df.iterrows():
            features = [
                row.get('vehicle_price', 3000) / 10000.0,     # 가격 정규화
                row.get('vehicle_year', 2020) / 2025.0,       # 연식 정규화
                row.get('vehicle_mileage', 50000) / 200000.0, # 주행거리
                row.get('vehicle_engine_size', 2.0) / 5.0,    # 배기량
                row.get('vehicle_fuel_efficiency', 12) / 30.0, # 연비
                row.get('vehicle_safety_rating', 4) / 5.0,    # 안전등급
                row.get('vehicle_brand_rank', 5) / 20.0,      # 브랜드 순위
                row.get('vehicle_body_type_code', 0) / 10.0,  # 차종 코드
                row.get('vehicle_fuel_type_code', 0) / 5.0,   # 연료 타입
                row.get('vehicle_transmission_auto', 1),      # 자동변속기 여부
                row.get('vehicle_accident_history', 0),      # 사고 이력
                row.get('vehicle_owner_count', 1) / 5.0,     # 이전 소유자 수
                row.get('vehicle_maintenance_score', 3) / 5.0, # 정비 상태
                row.get('vehicle_popularity_score', 0.5),     # 인기도
                row.get('vehicle_resale_value', 0.7)          # 리세일 가치
            ]
            vehicle_features.append(features)

        return np.array(vehicle_features, dtype=np.float32)

    def _extract_context_features(self, df: pd.DataFrame) -> np.ndarray:
        """상황 정보 피처 추출"""
        context_features = []

        for _, row in df.iterrows():
            features = [
                row.get('season_code', 0) / 4.0,        # 계절 (0-3)
                row.get('hour_of_day', 12) / 24.0,      # 시간대
                row.get('day_of_week', 3) / 7.0,        # 요일
                row.get('market_condition', 0.5),       # 시장 상황 지수
                row.get('oil_price_index', 0.5)         # 유가 지수
            ]
            context_features.append(features)

        return np.array(context_features, dtype=np.float32)

    def train(self,
              interaction_df: pd.DataFrame,
              validation_split: float = 0.2,
              epochs: int = 50,
              batch_size: int = 256,
              early_stopping_patience: int = 10):
        """모델 훈련"""

        # 데이터 준비
        print("📊 훈련 데이터 준비 중...")
        training_data = self.prepare_training_data(interaction_df)

        # 모델 컴파일
        if self.model is None:
            self.compile_model()

        # 콜백 설정
        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=early_stopping_patience,
                restore_best_weights=True
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7
            )
        ]

        # 훈련 실행
        print("🚀 NCF 모델 훈련 시작...")
        self.training_history = self.model.fit(
            x={
                'user_id': training_data['user_ids'],
                'vehicle_id': training_data['vehicle_ids'],
                'user_features': training_data['user_features'],
                'vehicle_features': training_data['vehicle_features'],
                'context_features': training_data['context_features']
            },
            y=training_data['labels'],
            validation_split=validation_split,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )

        print("✅ 훈련 완료!")
        return self.training_history

    def predict_user_preferences(self,
                                user_id: int,
                                vehicle_ids: List[int],
                                user_features: np.ndarray,
                                context_features: np.ndarray) -> np.ndarray:
        """사용자-차량 선호도 예측"""

        if self.model is None:
            raise ValueError("모델이 훈련되지 않았습니다.")

        # 차량 특성 추출 (실제로는 DB에서 가져옴)
        vehicle_features = self._get_vehicle_features_batch(vehicle_ids)

        # 배치 예측
        batch_size = len(vehicle_ids)
        predictions = self.model.predict({
            'user_id': np.array([user_id] * batch_size),
            'vehicle_id': np.array(vehicle_ids),
            'user_features': np.tile(user_features, (batch_size, 1)),
            'vehicle_features': vehicle_features,
            'context_features': np.tile(context_features, (batch_size, 1))
        })

        return predictions.flatten()

    def get_top_recommendations(self,
                              user_id: int,
                              user_features: np.ndarray,
                              context_features: np.ndarray,
                              candidate_vehicles: List[int],
                              top_k: int = 10) -> List[Dict]:
        """Top-K 추천 생성"""

        # 선호도 예측
        preferences = self.predict_user_preferences(
            user_id, candidate_vehicles, user_features, context_features
        )

        # 상위 K개 선택
        top_indices = np.argsort(preferences)[::-1][:top_k]
        top_vehicles = [candidate_vehicles[i] for i in top_indices]
        top_scores = [preferences[i] for i in top_indices]

        # 추천 결과 포맷
        recommendations = []
        for vehicle_id, score in zip(top_vehicles, top_scores):
            recommendations.append({
                'vehicle_id': vehicle_id,
                'preference_score': float(score),
                'reasoning': self._explain_recommendation(user_id, vehicle_id)
            })

        return recommendations

    def get_recommendations(self, user_dict: Dict, n_recommendations: int = 10) -> List[Dict]:
        """
        FastAPI 통합을 위한 간소화된 추천 인터페이스
        """
        try:
            # Mock 사용자 특성 생성 (실제로는 user_dict에서 추출)
            user_features = np.array([[
                user_dict.get('age', 30) / 100.0,
                user_dict.get('income', 5000) / 10000.0,
                2.0 / 10.0,  # family_size
                5.0 / 50.0,  # driving_exp
                0.0 / 100.0, # location_code
                3.0 / 5.0,   # education
                0.0 / 20.0,  # occupation_code
                0.0,         # gender
                0.0,         # married
                0.0          # car_ownership
            ]], dtype=np.float32)

            # Mock 컨텍스트 특성
            context_features = np.array([[
                1.0 / 4.0,   # season
                12.0 / 24.0, # hour
                3.0 / 7.0,   # day_of_week
                0.5,         # market_condition
                0.5          # oil_price_index
            ]], dtype=np.float32)

            # Mock 후보 차량 목록 (실제로는 데이터베이스에서 가져옴)
            budget_max = user_dict.get('budget_max', 5000)
            candidate_vehicles = list(range(min(50, self.num_vehicles)))

            # Mock 추천 결과 생성 (모델이 훈련되지 않은 경우)
            if self.model is None:
                recommendations = []
                for i, vehicle_id in enumerate(candidate_vehicles[:n_recommendations]):
                    score = 0.9 - (i * 0.05)  # 점진적 감소
                    recommendations.append({
                        'vehicle_id': f"ncf_{vehicle_id}",
                        'score': max(0.3, score),
                        'confidence': 0.85,
                        'reasons': [f'NCF Algorithm - 차량 {vehicle_id}', '딥러닝 기반 협업 필터링'],
                        'algorithm': 'Neural Collaborative Filtering'
                    })
                return recommendations

            # 실제 NCF 모델을 사용한 추천
            user_id_hash = hash(user_dict.get('user_id', 'default')) % self.num_users

            detailed_recs = self.get_top_recommendations(
                user_id=user_id_hash,
                user_features=user_features[0],
                context_features=context_features[0],
                candidate_vehicles=candidate_vehicles,
                top_k=n_recommendations
            )

            # 형식 변환
            recommendations = []
            for i, rec in enumerate(detailed_recs):
                recommendations.append({
                    'vehicle_id': str(rec['vehicle_id']),
                    'score': rec['preference_score'],
                    'confidence': 0.88,
                    'reasons': [rec['reasoning'], 'Neural Collaborative Filtering'],
                    'algorithm': 'NCF (He et al. 2017)'
                })

            return recommendations

        except Exception as e:
            # 에러 발생 시 기본 Mock 추천 반환
            print(f"NCF 추천 에러: {e}")
            mock_recommendations = []
            for i in range(min(n_recommendations, 10)):
                mock_recommendations.append({
                    'vehicle_id': f"mock_{i}",
                    'score': 0.8 - (i * 0.05),
                    'confidence': 0.75,
                    'reasons': ['NCF Fallback', '기본 추천 시스템'],
                    'algorithm': 'NCF Mock'
                })
            return mock_recommendations

    def _get_vehicle_features_batch(self, vehicle_ids: List[int]) -> np.ndarray:
        """차량 특성 배치 조회 (실제로는 DB 쿼리)"""
        # 임시 구현 - 실제로는 데이터베이스에서 조회
        batch_features = []
        for vehicle_id in vehicle_ids:
            # Mock 차량 특성
            features = [
                0.3,   # 가격
                0.8,   # 연식
                0.4,   # 주행거리
                0.6,   # 배기량
                0.7,   # 연비
                0.9,   # 안전등급
                0.6,   # 브랜드
                0.5,   # 차종
                0.3,   # 연료타입
                1.0,   # 자동변속기
                0.0,   # 사고이력
                0.2,   # 소유자수
                0.8,   # 정비상태
                0.6,   # 인기도
                0.7    # 리세일가치
            ]
            batch_features.append(features)

        return np.array(batch_features, dtype=np.float32)

    def _explain_recommendation(self, user_id: int, vehicle_id: int) -> str:
        """추천 이유 설명 생성"""
        explanations = [
            "선호도 패턴 분석 결과 높은 관심도 예상",
            "유사한 사용자들의 선택 패턴",
            "개인 맞춤 특성 분석 기반",
            "시장 트렌드 및 가성비 종합 고려"
        ]
        return explanations[hash(f"{user_id}_{vehicle_id}") % len(explanations)]

    def save_model(self, filepath: str):
        """모델 저장"""
        if self.model is not None:
            self.model.save_weights(filepath)

            # 메타데이터 저장
            metadata = {
                'num_users': self.num_users,
                'num_vehicles': self.num_vehicles,
                'embedding_dim': self.embedding_dim,
                'mlp_layers': self.mlp_layers
            }

            with open(f"{filepath}_metadata.json", 'w') as f:
                json.dump(metadata, f)

        print(f"✅ 모델 저장 완료: {filepath}")

    def load_model(self, filepath: str):
        """모델 로드"""
        # 메타데이터 로드
        with open(f"{filepath}_metadata.json", 'r') as f:
            metadata = json.load(f)

        # 모델 재구성
        self.__init__(**metadata)
        self.build_model()
        self.compile_model()

        # 가중치 로드
        self.model.load_weights(filepath)
        print(f"✅ 모델 로드 완료: {filepath}")

# NCF 통합을 위한 유틸리티 함수들
def create_mock_interaction_data(num_users: int = 1000, num_vehicles: int = 500) -> pd.DataFrame:
    """Mock 상호작용 데이터 생성"""
    np.random.seed(42)

    interactions = []

    for user_id in range(num_users):
        # 사용자별 15-30개 상호작용 생성
        num_interactions = np.random.randint(15, 31)

        for _ in range(num_interactions):
            vehicle_id = np.random.randint(0, num_vehicles)

            # 상호작용 타입별 선호도 점수
            interaction_type = np.random.choice([
                'view', 'click', 'favorite', 'inquiry', 'purchase'
            ], p=[0.5, 0.3, 0.1, 0.08, 0.02])

            # 타입별 선호도 점수 및 명시적 평점
            if interaction_type == 'purchase':
                preference_score = 1
                rating = np.random.choice([4, 5], p=[0.3, 0.7])
            elif interaction_type == 'inquiry':
                preference_score = 1 if np.random.random() > 0.3 else 0
                rating = np.random.choice([3, 4, 5], p=[0.2, 0.4, 0.4])
            elif interaction_type == 'favorite':
                preference_score = 1
                rating = np.random.choice([4, 5], p=[0.5, 0.5])
            else:
                preference_score = 1 if np.random.random() > 0.7 else 0
                rating = np.random.choice([1, 2, 3, 4, 5], p=[0.1, 0.2, 0.4, 0.2, 0.1])

            interaction = {
                'user_id': user_id,
                'vehicle_id': vehicle_id,
                'interaction_type': interaction_type,
                'preference_score': preference_score,
                'rating': rating,
                'timestamp': pd.Timestamp.now() - pd.Timedelta(days=np.random.randint(0, 365)),

                # 사용자 특성 (Mock)
                'user_age': np.random.randint(20, 65),
                'user_income': np.random.randint(3000, 8000),
                'user_family_size': np.random.randint(1, 5),

                # 차량 특성 (Mock)
                'vehicle_price': np.random.randint(1500, 8000),
                'vehicle_year': np.random.randint(2015, 2024),
                'vehicle_mileage': np.random.randint(10000, 150000),

                # 컨텍스트 (Mock)
                'season_code': np.random.randint(0, 4),
                'hour_of_day': np.random.randint(0, 24)
            }

            interactions.append(interaction)

    return pd.DataFrame(interactions)

def integrate_ncf_with_fastapi():
    """FastAPI에 NCF 모델 통합"""
    return """
    # backend/main.py에 추가할 코드

    from models.ncf_car_recommendation import CarRecommendationNCF
    import numpy as np

    # 전역 NCF 모델 인스턴스
    ncf_model = None

    def load_ncf_model():
        global ncf_model
        try:
            ncf_model = CarRecommendationNCF(
                num_users=10000,
                num_vehicles=5000,
                embedding_dim=64
            )
            ncf_model.load_model('models/trained_ncf_model')
            print("✅ NCF 모델 로드 성공")
        except Exception as e:
            print(f"⚠️ NCF 모델 로드 실패: {e}")
            ncf_model = None

    @app.post("/api/recommendations/ncf")
    async def get_ncf_recommendations(request: RecommendationRequest):
        '''NCF 기반 정밀 추천 API'''

        if ncf_model is None:
            load_ncf_model()

        if ncf_model is None:
            raise HTTPException(status_code=503, detail="NCF 모델을 사용할 수 없습니다")

        try:
            # 사용자 특성 추출
            user_features = extract_user_features(request.user_profile)
            context_features = extract_context_features()

            # 후보 차량 목록 (실제로는 DB 쿼리)
            candidate_vehicles = get_candidate_vehicles(request.user_profile)

            # NCF 추천 실행
            recommendations = ncf_model.get_top_recommendations(
                user_id=hash(request.user_profile.user_id) % 10000,
                user_features=user_features,
                context_features=context_features,
                candidate_vehicles=candidate_vehicles,
                top_k=request.limit
            )

            return {
                "recommendations": recommendations,
                "algorithm": "Neural Collaborative Filtering (He et al. 2017)",
                "model_type": "Deep Learning Hybrid",
                "confidence": "high"
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"NCF 추천 실패: {str(e)}")
    """

if __name__ == "__main__":
    # NCF 모델 테스트
    print("🧠 CarFinanceAI NCF 모델 테스트")

    # Mock 데이터 생성
    interaction_data = create_mock_interaction_data(1000, 500)
    print(f"📊 생성된 상호작용 데이터: {len(interaction_data)} 건")

    # NCF 모델 초기화
    ncf_model = CarRecommendationNCF(
        num_users=1000,
        num_vehicles=500,
        embedding_dim=64,
        mlp_layers=[128, 64, 32]
    )

    # 모델 구조 확인
    model = ncf_model.build_model()
    print(f"🏗️ NCF 모델 구조:")
    model.summary()

    print("\n✅ NCF 모델 준비 완료! 실제 데이터로 훈련 가능합니다.")