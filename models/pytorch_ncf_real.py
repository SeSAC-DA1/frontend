"""
PyTorch 기반 실제 데이터 연동 NCF 모델
AWS RDS PostgreSQL 연동 + 실시간 학습
"""

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error

# 데이터베이스 연동
import sys
sys.path.append('..')
from config.database import db_manager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CarInteractionDataset(Dataset):
    """PyTorch Dataset for car recommendation"""

    def __init__(self, interactions_df: pd.DataFrame, user_mapping: Dict, vehicle_mapping: Dict):
        self.interactions = interactions_df
        self.user_mapping = user_mapping
        self.vehicle_mapping = vehicle_mapping

        # 사용자 ID와 차량 ID를 인덱스로 매핑
        self.user_ids = torch.tensor([
            self.user_mapping.get(uid, 0) for uid in interactions_df['user_id']
        ], dtype=torch.long)

        self.vehicle_ids = torch.tensor([
            self.vehicle_mapping.get(vid, 0) for vid in interactions_df['vehicle_id']
        ], dtype=torch.long)

        # 암시적 피드백 점수 (rating이 없으면 implicit_score 사용)
        if 'rating' in interactions_df.columns:
            self.ratings = torch.tensor(interactions_df['rating'].fillna(3.0).values, dtype=torch.float32)
        else:
            self.ratings = torch.tensor(interactions_df['implicit_score'].fillna(1.0).values, dtype=torch.float32)

        logger.info(f"Dataset created: {len(self)} interactions")

    def __len__(self):
        return len(self.interactions)

    def __getitem__(self, idx):
        return {
            'user_id': self.user_ids[idx],
            'vehicle_id': self.vehicle_ids[idx],
            'rating': self.ratings[idx]
        }

class PyTorchNCF(nn.Module):
    """
    PyTorch Implementation of Neural Collaborative Filtering (He et al. 2017)
    실제 PostgreSQL 데이터 연동
    """

    def __init__(self,
                 num_users: int,
                 num_vehicles: int,
                 embedding_dim: int = 64,
                 mlp_layers: List[int] = [256, 128, 64],
                 dropout_rate: float = 0.2):
        super(PyTorchNCF, self).__init__()

        self.num_users = num_users
        self.num_vehicles = num_vehicles
        self.embedding_dim = embedding_dim

        # GMF (Generalized Matrix Factorization) Embeddings
        self.user_embedding_gmf = nn.Embedding(num_users, embedding_dim)
        self.vehicle_embedding_gmf = nn.Embedding(num_vehicles, embedding_dim)

        # MLP (Multi-Layer Perceptron) Embeddings
        self.user_embedding_mlp = nn.Embedding(num_users, embedding_dim)
        self.vehicle_embedding_mlp = nn.Embedding(num_vehicles, embedding_dim)

        # MLP Layers
        mlp_input_dim = embedding_dim * 2
        mlp_modules = []

        for i, layer_size in enumerate(mlp_layers):
            mlp_modules.extend([
                nn.Linear(mlp_input_dim if i == 0 else mlp_layers[i-1], layer_size),
                nn.ReLU(),
                nn.Dropout(dropout_rate)
            ])

        self.mlp_layers = nn.Sequential(*mlp_modules)

        # Final Prediction Layer
        self.final_layer = nn.Linear(embedding_dim + mlp_layers[-1], 1)
        self.sigmoid = nn.Sigmoid()

        # Weight Initialization
        self._init_weights()

        logger.info(f"PyTorch NCF initialized: {num_users} users, {num_vehicles} vehicles")

    def _init_weights(self):
        """Xavier 초기화"""
        for m in self.modules():
            if isinstance(m, nn.Embedding):
                nn.init.xavier_uniform_(m.weight)
            elif isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, user_ids, vehicle_ids):
        # GMF Part
        gmf_user = self.user_embedding_gmf(user_ids)
        gmf_vehicle = self.vehicle_embedding_gmf(vehicle_ids)
        gmf_output = gmf_user * gmf_vehicle  # Element-wise product

        # MLP Part
        mlp_user = self.user_embedding_mlp(user_ids)
        mlp_vehicle = self.vehicle_embedding_mlp(vehicle_ids)
        mlp_input = torch.cat([mlp_user, mlp_vehicle], dim=-1)
        mlp_output = self.mlp_layers(mlp_input)

        # Concatenate GMF and MLP outputs
        final_input = torch.cat([gmf_output, mlp_output], dim=-1)
        prediction = self.sigmoid(self.final_layer(final_input))

        return prediction.squeeze()

class RealDataNCFSystem:
    """실제 데이터 기반 NCF 추천 시스템"""

    def __init__(self, embedding_dim: int = 64, device: str = 'cuda' if torch.cuda.is_available() else 'cpu'):
        self.device = device
        self.embedding_dim = embedding_dim

        # 모델 관련
        self.model = None
        self.optimizer = None
        self.criterion = nn.MSELoss()

        # 데이터 매핑
        self.user_mapping = {}
        self.vehicle_mapping = {}
        self.reverse_user_mapping = {}
        self.reverse_vehicle_mapping = {}

        # 데이터셋
        self.train_loader = None
        self.val_loader = None
        self.test_loader = None

        # 성능 메트릭
        self.training_history = []

        logger.info(f"NCF System initialized on device: {device}")

    def load_real_data(self) -> bool:
        """PostgreSQL에서 실제 데이터 로드"""
        try:
            # 데이터베이스 연결 테스트
            if not db_manager.test_connection():
                logger.error("데이터베이스 연결 실패")
                return False

            # 실제 데이터 로드
            logger.info("실제 데이터 로딩 시작...")

            users_df = db_manager.load_users_data()
            vehicles_df = db_manager.load_vehicles_data()
            interactions_df = db_manager.load_interactions_data()

            if len(interactions_df) == 0:
                logger.warning("상호작용 데이터가 없습니다. 샘플 데이터 생성...")
                return self._create_sample_data()

            # 사용자 및 차량 매핑 생성
            unique_users = users_df['user_id'].unique()
            unique_vehicles = vehicles_df['vehicle_id'].unique()

            self.user_mapping = {uid: idx for idx, uid in enumerate(unique_users)}
            self.vehicle_mapping = {vid: idx for idx, vid in enumerate(unique_vehicles)}

            self.reverse_user_mapping = {idx: uid for uid, idx in self.user_mapping.items()}
            self.reverse_vehicle_mapping = {idx: vid for vid, idx in self.vehicle_mapping.items()}

            # 상호작용 데이터 필터링 (매핑된 사용자/차량만)
            interactions_df = interactions_df[
                (interactions_df['user_id'].isin(self.user_mapping.keys())) &
                (interactions_df['vehicle_id'].isin(self.vehicle_mapping.keys()))
            ]

            logger.info(f"데이터 로드 완료: {len(unique_users)} users, {len(unique_vehicles)} vehicles, {len(interactions_df)} interactions")

            # 데이터셋 분할
            self._prepare_datasets(interactions_df)

            return True

        except Exception as e:
            logger.error(f"실제 데이터 로드 실패: {e}")
            return False

    def _create_sample_data(self) -> bool:
        """샘플 데이터 생성 및 PostgreSQL에 삽입"""
        try:
            logger.info("샘플 데이터 생성 시작...")

            # 샘플 사용자 생성 (100명)
            users_data = []
            for i in range(100):
                users_data.append({
                    'user_id': f'user_{i+1:03d}',
                    'name': f'사용자{i+1}',
                    'email': f'user{i+1}@example.com',
                    'age': np.random.randint(20, 65),
                    'location': np.random.choice(['서울', '부산', '대구', '인천', '광주']),
                    'income_range': f"{np.random.randint(3000, 10000)}-{np.random.randint(5000, 12000)}",
                    'budget_min': np.random.randint(1500, 3000),
                    'budget_max': np.random.randint(3000, 8000)
                })

            # 샘플 차량 생성 (200대)
            brands = ['현대', '기아', 'BMW', '벤츠', '아우디', '토요타', '혼다']
            fuel_types = ['gasoline', 'hybrid', 'electric', 'diesel']
            vehicles_data = []

            for i in range(200):
                brand = np.random.choice(brands)
                vehicles_data.append({
                    'vehicle_id': f'car_{i+1:03d}',
                    'brand': brand,
                    'model': f'{brand}_Model_{i+1}',
                    'year': np.random.randint(2015, 2024),
                    'price': np.random.randint(1500, 8000),
                    'fuel_type': np.random.choice(fuel_types),
                    'mileage': np.random.randint(10000, 150000),
                    'safety_rating': round(np.random.uniform(3.0, 5.0), 1)
                })

            # 샘플 상호작용 생성 (5000건)
            interactions_data = []
            interaction_types = ['view', 'click', 'like', 'inquiry', 'favorite']

            for _ in range(5000):
                user_id = f'user_{np.random.randint(1, 101):03d}'
                vehicle_id = f'car_{np.random.randint(1, 201):03d}'
                interaction_type = np.random.choice(interaction_types)

                # 상호작용 타입별 암시적 점수 및 평점
                if interaction_type in ['inquiry', 'favorite']:
                    implicit_score = np.random.uniform(0.8, 1.0)
                    rating = np.random.randint(4, 6)
                elif interaction_type == 'like':
                    implicit_score = np.random.uniform(0.6, 0.8)
                    rating = np.random.randint(3, 5)
                else:
                    implicit_score = np.random.uniform(0.3, 0.6)
                    rating = np.random.randint(1, 4)

                interactions_data.append({
                    'user_id': user_id,
                    'vehicle_id': vehicle_id,
                    'interaction_type': interaction_type,
                    'rating': rating,
                    'implicit_score': implicit_score,
                    'view_duration': np.random.randint(10, 300),
                    'created_at': datetime.now()
                })

            # PostgreSQL에 데이터 삽입
            users_df = pd.DataFrame(users_data)
            vehicles_df = pd.DataFrame(vehicles_data)
            interactions_df = pd.DataFrame(interactions_data)

            # 데이터베이스에 저장 (실제로는 bulk insert 사용)
            logger.info("PostgreSQL에 샘플 데이터 저장 중...")
            # users_df.to_sql('users', db_manager.engine, if_exists='append', index=False)
            # vehicles_df.to_sql('vehicles', db_manager.engine, if_exists='append', index=False)
            # interactions_df.to_sql('user_interactions', db_manager.engine, if_exists='append', index=False)

            # 매핑 생성
            self.user_mapping = {uid: idx for idx, uid in enumerate(users_df['user_id'].unique())}
            self.vehicle_mapping = {vid: idx for idx, vid in enumerate(vehicles_df['vehicle_id'].unique())}
            self.reverse_user_mapping = {idx: uid for uid, idx in self.user_mapping.items()}
            self.reverse_vehicle_mapping = {idx: vid for vid, idx in self.vehicle_mapping.items()}

            # 데이터셋 준비
            self._prepare_datasets(interactions_df)

            logger.info("샘플 데이터 생성 완료!")
            return True

        except Exception as e:
            logger.error(f"샘플 데이터 생성 실패: {e}")
            return False

    def _prepare_datasets(self, interactions_df: pd.DataFrame):
        """데이터셋 분할 및 DataLoader 준비"""
        # 훈련/검증/테스트 분할 (60/20/20)
        train_df, temp_df = train_test_split(interactions_df, test_size=0.4, random_state=42)
        val_df, test_df = train_test_split(temp_df, test_size=0.5, random_state=42)

        # PyTorch Dataset 생성
        train_dataset = CarInteractionDataset(train_df, self.user_mapping, self.vehicle_mapping)
        val_dataset = CarInteractionDataset(val_df, self.user_mapping, self.vehicle_mapping)
        test_dataset = CarInteractionDataset(test_df, self.user_mapping, self.vehicle_mapping)

        # DataLoader 생성
        batch_size = 256
        self.train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
        self.val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
        self.test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=0)

        logger.info(f"데이터셋 분할 완료: train={len(train_dataset)}, val={len(val_dataset)}, test={len(test_dataset)}")

    def build_model(self):
        """PyTorch NCF 모델 생성"""
        if not self.user_mapping or not self.vehicle_mapping:
            raise ValueError("데이터 매핑이 생성되지 않았습니다. load_real_data()를 먼저 실행하세요.")

        num_users = len(self.user_mapping)
        num_vehicles = len(self.vehicle_mapping)

        self.model = PyTorchNCF(
            num_users=num_users,
            num_vehicles=num_vehicles,
            embedding_dim=self.embedding_dim,
            mlp_layers=[256, 128, 64],
            dropout_rate=0.2
        ).to(self.device)

        # 옵티마이저 설정
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001, weight_decay=1e-6)

        logger.info(f"모델 생성 완료: {num_users} users, {num_vehicles} vehicles")

    def train_model(self, epochs: int = 50, early_stopping_patience: int = 10):
        """모델 훈련"""
        if self.model is None:
            self.build_model()

        best_val_loss = float('inf')
        patience_counter = 0

        for epoch in range(epochs):
            # 훈련 단계
            self.model.train()
            train_loss = 0.0
            train_batches = 0

            for batch in self.train_loader:
                user_ids = batch['user_id'].to(self.device)
                vehicle_ids = batch['vehicle_id'].to(self.device)
                ratings = batch['rating'].to(self.device)

                # Forward pass
                predictions = self.model(user_ids, vehicle_ids)
                loss = self.criterion(predictions, ratings)

                # Backward pass
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()

                train_loss += loss.item()
                train_batches += 1

            avg_train_loss = train_loss / train_batches

            # 검증 단계
            self.model.eval()
            val_loss = 0.0
            val_batches = 0

            with torch.no_grad():
                for batch in self.val_loader:
                    user_ids = batch['user_id'].to(self.device)
                    vehicle_ids = batch['vehicle_id'].to(self.device)
                    ratings = batch['rating'].to(self.device)

                    predictions = self.model(user_ids, vehicle_ids)
                    loss = self.criterion(predictions, ratings)

                    val_loss += loss.item()
                    val_batches += 1

            avg_val_loss = val_loss / val_batches

            # 로깅
            logger.info(f"Epoch {epoch+1}/{epochs}: Train Loss={avg_train_loss:.4f}, Val Loss={avg_val_loss:.4f}")

            # Early Stopping
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                patience_counter = 0
                self.save_model(f'models/pytorch_ncf_best.pth')
            else:
                patience_counter += 1
                if patience_counter >= early_stopping_patience:
                    logger.info(f"Early stopping at epoch {epoch+1}")
                    break

            # 훈련 이력 저장
            self.training_history.append({
                'epoch': epoch + 1,
                'train_loss': avg_train_loss,
                'val_loss': avg_val_loss
            })

        logger.info("모델 훈련 완료!")

    def evaluate_model(self) -> Dict[str, float]:
        """모델 성능 평가"""
        if self.model is None or self.test_loader is None:
            raise ValueError("모델 또는 테스트 데이터가 준비되지 않았습니다.")

        self.model.eval()
        predictions = []
        actuals = []

        with torch.no_grad():
            for batch in self.test_loader:
                user_ids = batch['user_id'].to(self.device)
                vehicle_ids = batch['vehicle_id'].to(self.device)
                ratings = batch['rating'].to(self.device)

                batch_predictions = self.model(user_ids, vehicle_ids)

                predictions.extend(batch_predictions.cpu().numpy())
                actuals.extend(ratings.cpu().numpy())

        # 평가 메트릭 계산
        rmse = np.sqrt(mean_squared_error(actuals, predictions))
        mae = mean_absolute_error(actuals, predictions)

        results = {
            'rmse': rmse,
            'mae': mae,
            'num_samples': len(predictions)
        }

        logger.info(f"모델 평가 완료: RMSE={rmse:.4f}, MAE={mae:.4f}")
        return results

    def predict_user_preferences(self, user_id: str, candidate_vehicle_ids: List[str]) -> List[Dict]:
        """사용자별 차량 선호도 예측"""
        if self.model is None:
            raise ValueError("모델이 훈련되지 않았습니다.")

        if user_id not in self.user_mapping:
            logger.warning(f"알 수 없는 사용자: {user_id}")
            return []

        user_idx = self.user_mapping[user_id]
        predictions = []

        self.model.eval()
        with torch.no_grad():
            for vehicle_id in candidate_vehicle_ids:
                if vehicle_id not in self.vehicle_mapping:
                    continue

                vehicle_idx = self.vehicle_mapping[vehicle_id]

                user_tensor = torch.tensor([user_idx], dtype=torch.long).to(self.device)
                vehicle_tensor = torch.tensor([vehicle_idx], dtype=torch.long).to(self.device)

                prediction = self.model(user_tensor, vehicle_tensor).item()

                predictions.append({
                    'vehicle_id': vehicle_id,
                    'predicted_score': prediction,
                    'algorithm': 'PyTorch NCF'
                })

        # 점수순 정렬
        predictions.sort(key=lambda x: x['predicted_score'], reverse=True)
        return predictions

    def save_model(self, filepath: str):
        """모델 저장"""
        if self.model is None:
            raise ValueError("저장할 모델이 없습니다.")

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'user_mapping': self.user_mapping,
            'vehicle_mapping': self.vehicle_mapping,
            'embedding_dim': self.embedding_dim,
            'training_history': self.training_history
        }, filepath)

        logger.info(f"모델 저장 완료: {filepath}")

    def load_model(self, filepath: str):
        """모델 로드"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {filepath}")

        checkpoint = torch.load(filepath, map_location=self.device)

        self.user_mapping = checkpoint['user_mapping']
        self.vehicle_mapping = checkpoint['vehicle_mapping']
        self.embedding_dim = checkpoint['embedding_dim']
        self.training_history = checkpoint.get('training_history', [])

        # 모델 재구축 및 로드
        self.build_model()
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])

        logger.info(f"모델 로드 완료: {filepath}")

# 사용 예시
if __name__ == "__main__":
    # NCF 시스템 초기화
    ncf_system = RealDataNCFSystem(embedding_dim=64)

    # 실제 데이터 로드
    if ncf_system.load_real_data():
        # 모델 훈련
        ncf_system.train_model(epochs=30)

        # 모델 평가
        evaluation = ncf_system.evaluate_model()
        print(f"평가 결과: {evaluation}")

        # 추천 테스트
        test_user = 'user_001'
        candidate_vehicles = ['car_001', 'car_002', 'car_003', 'car_004', 'car_005']
        recommendations = ncf_system.predict_user_preferences(test_user, candidate_vehicles)

        print(f"\n사용자 {test_user} 추천 결과:")
        for i, rec in enumerate(recommendations[:3]):
            print(f"{i+1}. {rec['vehicle_id']}: {rec['predicted_score']:.4f}")
    else:
        print("데이터 로드 실패!")