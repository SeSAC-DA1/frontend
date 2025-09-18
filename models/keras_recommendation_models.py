"""
Keras 기반 추천시스템 모델 컬렉션
Deep Learning for Recommender Systems

모델 구현:
1. Neural Collaborative Filtering (He et al. 2017)
2. Wide & Deep Learning (Cheng et al. 2016)
3. Deep Crossing (Shan et al. 2016)
4. DeepFM (Guo et al. 2017)
5. AutoRec (Sedhain et al. 2015)
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model, Input
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from typing import Dict, List, Tuple, Optional
import logging

class KerasRecommendationModels:
    """Keras 기반 추천시스템 모델 컬렉션"""

    def __init__(self, n_users: int, n_items: int, embedding_dim: int = 64):
        self.n_users = n_users
        self.n_items = n_items
        self.embedding_dim = embedding_dim
        self.models = {}
        self.logger = self._setup_logger()

    def _setup_logger(self):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)

    def build_neural_cf(self,
                       gmf_dim: int = 64,
                       mlp_dims: List[int] = [128, 64, 32],
                       dropout_rate: float = 0.2) -> Model:
        """
        Neural Collaborative Filtering (He et al. 2017)

        아키텍처:
        - GMF (Generalized Matrix Factorization)
        - MLP (Multi-Layer Perceptron)
        - NeuMF (Neural Matrix Factorization)
        """

        # 입력 레이어
        user_input = Input(shape=(), name='user_id', dtype='int32')
        item_input = Input(shape=(), name='item_id', dtype='int32')

        # GMF 브랜치
        user_embedding_gmf = layers.Embedding(
            self.n_users, gmf_dim,
            embeddings_initializer='he_normal',
            embeddings_regularizer=keras.regularizers.l2(1e-6),
            name='user_embedding_gmf'
        )(user_input)

        item_embedding_gmf = layers.Embedding(
            self.n_items, gmf_dim,
            embeddings_initializer='he_normal',
            embeddings_regularizer=keras.regularizers.l2(1e-6),
            name='item_embedding_gmf'
        )(item_input)

        user_vec_gmf = layers.Flatten(name='user_flatten_gmf')(user_embedding_gmf)
        item_vec_gmf = layers.Flatten(name='item_flatten_gmf')(item_embedding_gmf)

        # GMF 출력: element-wise product
        gmf_output = layers.Multiply(name='gmf_multiply')([user_vec_gmf, item_vec_gmf])

        # MLP 브랜치
        user_embedding_mlp = layers.Embedding(
            self.n_users, self.embedding_dim,
            embeddings_initializer='he_normal',
            embeddings_regularizer=keras.regularizers.l2(1e-6),
            name='user_embedding_mlp'
        )(user_input)

        item_embedding_mlp = layers.Embedding(
            self.n_items, self.embedding_dim,
            embeddings_initializer='he_normal',
            embeddings_regularizer=keras.regularizers.l2(1e-6),
            name='item_embedding_mlp'
        )(item_input)

        user_vec_mlp = layers.Flatten(name='user_flatten_mlp')(user_embedding_mlp)
        item_vec_mlp = layers.Flatten(name='item_flatten_mlp')(item_embedding_mlp)

        # MLP 입력: concatenation
        mlp_input = layers.Concatenate(name='mlp_concat')([user_vec_mlp, item_vec_mlp])

        # MLP 레이어들
        mlp_output = mlp_input
        for i, dim in enumerate(mlp_dims):
            mlp_output = layers.Dense(
                dim,
                activation='relu',
                kernel_initializer='he_normal',
                kernel_regularizer=keras.regularizers.l2(1e-6),
                name=f'mlp_dense_{i}'
            )(mlp_output)
            mlp_output = layers.Dropout(dropout_rate, name=f'mlp_dropout_{i}')(mlp_output)

        # NeuMF: GMF + MLP 결합
        neumf_input = layers.Concatenate(name='neumf_concat')([gmf_output, mlp_output])

        # 최종 출력 레이어
        output = layers.Dense(
            1,
            activation='linear',
            kernel_initializer='he_normal',
            name='prediction'
        )(neumf_input)

        model = Model(inputs=[user_input, item_input], outputs=output, name='NeuralCF')

        self.logger.info("✅ Neural Collaborative Filtering model built")
        return model

    def build_wide_and_deep(self,
                           wide_features: int,
                           deep_dims: List[int] = [256, 128, 64],
                           dropout_rate: float = 0.3) -> Model:
        """
        Wide & Deep Learning (Cheng et al. 2016)

        아키텍처:
        - Wide: Linear model (memorization)
        - Deep: DNN (generalization)
        """

        # 사용자/아이템 입력
        user_input = Input(shape=(), name='user_id', dtype='int32')
        item_input = Input(shape=(), name='item_id', dtype='int32')

        # Wide 부분을 위한 feature 입력
        wide_input = Input(shape=(wide_features,), name='wide_features')

        # Deep 부분: 임베딩
        user_embedding = layers.Embedding(
            self.n_users, self.embedding_dim,
            embeddings_initializer='he_normal',
            name='user_embedding'
        )(user_input)

        item_embedding = layers.Embedding(
            self.n_items, self.embedding_dim,
            embeddings_initializer='he_normal',
            name='item_embedding'
        )(item_input)

        user_vec = layers.Flatten()(user_embedding)
        item_vec = layers.Flatten()(item_embedding)

        # Deep 부분: DNN
        deep_input = layers.Concatenate(name='deep_concat')([user_vec, item_vec])

        deep_output = deep_input
        for i, dim in enumerate(deep_dims):
            deep_output = layers.Dense(
                dim,
                activation='relu',
                kernel_initializer='he_normal',
                kernel_regularizer=keras.regularizers.l2(1e-5),
                name=f'deep_dense_{i}'
            )(deep_output)
            deep_output = layers.Dropout(dropout_rate, name=f'deep_dropout_{i}')(deep_output)

        # Wide 부분: Linear layer
        wide_output = layers.Dense(
            1,
            activation='linear',
            kernel_initializer='glorot_uniform',
            name='wide_linear'
        )(wide_input)

        # Deep 부분 출력
        deep_final = layers.Dense(
            1,
            activation='linear',
            kernel_initializer='he_normal',
            name='deep_final'
        )(deep_output)

        # Wide & Deep 결합
        combined_output = layers.Add(name='wide_deep_add')([wide_output, deep_final])

        model = Model(
            inputs=[user_input, item_input, wide_input],
            outputs=combined_output,
            name='WideAndDeep'
        )

        self.logger.info("✅ Wide & Deep Learning model built")
        return model

    def build_deepfm(self,
                    field_dims: List[int],
                    embedding_dim: int = 64,
                    deep_dims: List[int] = [256, 128, 64],
                    dropout_rate: float = 0.2) -> Model:
        """
        DeepFM (Guo et al. 2017)

        아키텍처:
        - FM: Factorization Machine
        - Deep: DNN
        """

        # 필드별 입력 (사용자, 아이템, 기타 categorical features)
        inputs = []
        embeddings = []

        for i, field_dim in enumerate(field_dims):
            field_input = Input(shape=(), name=f'field_{i}', dtype='int32')
            inputs.append(field_input)

            # 임베딩 레이어
            embedding = layers.Embedding(
                field_dim, embedding_dim,
                embeddings_initializer='he_normal',
                embeddings_regularizer=keras.regularizers.l2(1e-6),
                name=f'embedding_{i}'
            )(field_input)
            embeddings.append(embedding)

        # FM 부분
        # First-order: linear terms
        linear_outputs = []
        for i, embedding in enumerate(embeddings):
            linear_part = layers.Dense(
                1,
                use_bias=False,
                kernel_initializer='he_normal',
                name=f'linear_{i}'
            )(layers.Flatten()(embedding))
            linear_outputs.append(linear_part)

        fm_first_order = layers.Add(name='fm_first_order')(linear_outputs)

        # Second-order: interaction terms
        # Sum of squares
        square_of_sum = layers.Add(name='square_of_sum')(embeddings)
        square_of_sum = tf.square(square_of_sum)

        # Sum of sum of squares
        sum_of_square = layers.Add(name='sum_of_square')([tf.square(emb) for emb in embeddings])

        # FM second order
        fm_second_order = 0.5 * (square_of_sum - sum_of_square)
        fm_second_order = layers.Dense(
            1,
            use_bias=False,
            kernel_initializer='he_normal',
            name='fm_second_order'
        )(layers.Flatten()(fm_second_order))

        # Deep 부분
        deep_input = layers.Concatenate(name='deep_input')([layers.Flatten()(emb) for emb in embeddings])

        deep_output = deep_input
        for i, dim in enumerate(deep_dims):
            deep_output = layers.Dense(
                dim,
                activation='relu',
                kernel_initializer='he_normal',
                kernel_regularizer=keras.regularizers.l2(1e-5),
                name=f'deep_{i}'
            )(deep_output)
            deep_output = layers.Dropout(dropout_rate, name=f'deep_dropout_{i}')(deep_output)

        deep_final = layers.Dense(
            1,
            activation='linear',
            kernel_initializer='he_normal',
            name='deep_output'
        )(deep_output)

        # DeepFM 출력: FM + Deep
        deepfm_output = layers.Add(name='deepfm_output')([fm_first_order, fm_second_order, deep_final])

        model = Model(inputs=inputs, outputs=deepfm_output, name='DeepFM')

        self.logger.info("✅ DeepFM model built")
        return model

    def build_autorec(self,
                     hidden_dims: List[int] = [256, 128],
                     activation: str = 'sigmoid',
                     dropout_rate: float = 0.1) -> Model:
        """
        AutoRec (Sedhain et al. 2015)

        아키텍처:
        - Autoencoder for collaborative filtering
        - Input: user-item interaction vector
        - Output: reconstructed interaction vector
        """

        # 입력: 사용자의 모든 아이템 평점 벡터
        input_layer = Input(shape=(self.n_items,), name='user_ratings')

        # Encoder
        encoded = input_layer
        for i, dim in enumerate(hidden_dims):
            encoded = layers.Dense(
                dim,
                activation=activation,
                kernel_initializer='he_normal',
                kernel_regularizer=keras.regularizers.l2(1e-5),
                name=f'encoder_{i}'
            )(encoded)
            encoded = layers.Dropout(dropout_rate, name=f'encoder_dropout_{i}')(encoded)

        # Decoder
        decoded = encoded
        for i, dim in enumerate(reversed(hidden_dims[:-1])):
            decoded = layers.Dense(
                dim,
                activation=activation,
                kernel_initializer='he_normal',
                kernel_regularizer=keras.regularizers.l2(1e-5),
                name=f'decoder_{i}'
            )(decoded)
            decoded = layers.Dropout(dropout_rate, name=f'decoder_dropout_{i}')(decoded)

        # 출력: 재구성된 평점 벡터
        output = layers.Dense(
            self.n_items,
            activation='linear',
            kernel_initializer='he_normal',
            name='reconstructed_ratings'
        )(decoded)

        model = Model(inputs=input_layer, outputs=output, name='AutoRec')

        self.logger.info("✅ AutoRec model built")
        return model

    def build_deep_crossing(self,
                           categorical_features: List[int],
                           numerical_features: int,
                           cross_layers: int = 3,
                           deep_dims: List[int] = [256, 128, 64]) -> Model:
        """
        Deep Crossing (Shan et al. 2016)

        아키텍처:
        - Residual units
        - Feature crossing at multiple levels
        """

        # Categorical feature 입력들
        categorical_inputs = []
        categorical_embeddings = []

        for i, vocab_size in enumerate(categorical_features):
            cat_input = Input(shape=(), name=f'categorical_{i}', dtype='int32')
            categorical_inputs.append(cat_input)

            embedding = layers.Embedding(
                vocab_size, self.embedding_dim,
                embeddings_initializer='he_normal',
                name=f'cat_embedding_{i}'
            )(cat_input)
            embedding = layers.Flatten()(embedding)
            categorical_embeddings.append(embedding)

        # Numerical feature 입력
        numerical_input = Input(shape=(numerical_features,), name='numerical_features')

        # 모든 feature 결합
        all_features = categorical_embeddings + [numerical_input]
        combined_features = layers.Concatenate(name='combined_features')(all_features)

        # Deep Crossing 레이어들
        x = combined_features

        for i in range(cross_layers):
            # Residual connection
            residual = x

            # Dense layer
            x = layers.Dense(
                deep_dims[0] if i == 0 else x.shape[-1],
                activation='relu',
                kernel_initializer='he_normal',
                name=f'cross_dense_{i}'
            )(x)

            # Residual connection (차원이 맞을 때만)
            if residual.shape[-1] == x.shape[-1]:
                x = layers.Add(name=f'cross_residual_{i}')([x, residual])

        # 최종 DNN
        for i, dim in enumerate(deep_dims):
            x = layers.Dense(
                dim,
                activation='relu',
                kernel_initializer='he_normal',
                kernel_regularizer=keras.regularizers.l2(1e-5),
                name=f'final_dense_{i}'
            )(x)
            x = layers.Dropout(0.2, name=f'final_dropout_{i}')(x)

        # 출력
        output = layers.Dense(
            1,
            activation='linear',
            kernel_initializer='he_normal',
            name='prediction'
        )(x)

        model = Model(
            inputs=categorical_inputs + [numerical_input],
            outputs=output,
            name='DeepCrossing'
        )

        self.logger.info("✅ Deep Crossing model built")
        return model

    def compile_model(self,
                     model: Model,
                     optimizer: str = 'adam',
                     learning_rate: float = 0.001,
                     loss: str = 'mse',
                     metrics: List[str] = ['mae']) -> Model:
        """모델 컴파일 (공통 설정)"""

        if optimizer == 'adam':
            opt = Adam(learning_rate=learning_rate, beta_1=0.9, beta_2=0.999, epsilon=1e-7)
        else:
            opt = optimizer

        model.compile(
            optimizer=opt,
            loss=loss,
            metrics=metrics
        )

        self.logger.info(f"✅ Model compiled - Optimizer: {optimizer}, Loss: {loss}")
        return model

    def get_callbacks(self,
                     patience: int = 10,
                     min_delta: float = 1e-4,
                     factor: float = 0.5) -> List:
        """훈련용 콜백 설정"""

        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=patience,
                min_delta=min_delta,
                restore_best_weights=True,
                verbose=1
            ),
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=factor,
                patience=patience // 2,
                min_lr=1e-7,
                verbose=1
            )
        ]

        return callbacks

    def train_model(self,
                   model: Model,
                   train_data: Tuple,
                   validation_data: Tuple,
                   epochs: int = 100,
                   batch_size: int = 256,
                   verbose: int = 1) -> Dict:
        """모델 훈련"""

        callbacks = self.get_callbacks()

        history = model.fit(
            train_data[0], train_data[1],
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=verbose
        )

        self.logger.info("✅ Model training completed")

        return {
            'model': model,
            'history': history,
            'best_val_loss': min(history.history['val_loss']),
            'best_epoch': np.argmin(history.history['val_loss']) + 1
        }

    def predict_batch(self,
                     model: Model,
                     user_ids: np.ndarray,
                     item_ids: np.ndarray) -> np.ndarray:
        """배치 예측"""

        predictions = model.predict([user_ids, item_ids], verbose=0)
        return predictions.flatten()

    def get_model_summary(self, model: Model) -> str:
        """모델 아키텍처 요약"""

        summary_lines = []
        model.summary(print_fn=lambda x: summary_lines.append(x))
        return '\n'.join(summary_lines)

# 사용 예시
if __name__ == "__main__":
    # 모델 빌더 초기화
    n_users, n_items = 1000, 5000
    models = KerasRecommendationModels(n_users, n_items)

    print("🧠 Keras Recommendation Models")
    print("=" * 50)

    # 1. Neural CF 모델
    ncf_model = models.build_neural_cf()
    ncf_model = models.compile_model(ncf_model)
    print(f"Neural CF 파라미터 수: {ncf_model.count_params():,}")

    # 2. Wide & Deep 모델
    wd_model = models.build_wide_and_deep(wide_features=20)
    wd_model = models.compile_model(wd_model)
    print(f"Wide & Deep 파라미터 수: {wd_model.count_params():,}")

    # 3. DeepFM 모델
    deepfm_model = models.build_deepfm(field_dims=[n_users, n_items, 100, 50])
    deepfm_model = models.compile_model(deepfm_model)
    print(f"DeepFM 파라미터 수: {deepfm_model.count_params():,}")

    # 4. AutoRec 모델
    autorec_model = models.build_autorec()
    autorec_model = models.compile_model(autorec_model)
    print(f"AutoRec 파라미터 수: {autorec_model.count_params():,}")

    print("\n✅ 모든 Keras 모델이 성공적으로 구성되었습니다!")