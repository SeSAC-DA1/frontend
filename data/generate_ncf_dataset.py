"""
NCF 모델을 위한 실제 차량 데이터셋 생성
- 사용자-차량 상호작용 매트릭스 생성
- 차량 특성 피처 생성
- 사용자 프로필 생성
"""
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import random

# 시드 고정
np.random.seed(42)
random.seed(42)

# 실제 차량 브랜드와 모델
REAL_CAR_DATA = {
    '현대': ['아반떼', '소나타', '그랜저', '투싼', '싼타페', 'i30', '벨로스터'],
    '기아': ['K3', 'K5', 'K7', '스포티지', '소렌토', '모하비', '스팅어'],
    '삼성': ['SM3', 'SM5', 'SM7', 'QM3', 'QM5', 'QM6'],
    'BMW': ['320i', '520i', 'X3', 'X5', '320d', '530i'],
    '벤츠': ['C200', 'E200', 'E300', 'GLC', 'GLE', 'S350'],
    '아우디': ['A4', 'A6', 'Q3', 'Q5', 'Q7', 'A3'],
    '토요타': ['캠리', '프리우스', '렉서스', 'RAV4', '하이랜더'],
    '혼다': ['어코드', '시빅', 'CR-V', 'HR-V'],
    '닛산': ['알티마', '센트라', '로그', '엑스트레일'],
    '폭스바겐': ['골프', '파사트', '티구안', '투아렉']
}

FUEL_TYPES = ['gasoline', 'hybrid', 'electric', 'diesel']
BODY_TYPES = ['sedan', 'suv', 'hatchback', 'coupe', 'wagon']
COLORS = ['white', 'black', 'silver', 'red', 'blue', 'gray']
LOCATIONS = ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '수원', '창원', '고양']

def generate_realistic_vehicle_dataset(n_vehicles=200):
    """실제와 유사한 차량 데이터셋 생성"""
    vehicles = []

    for i in range(n_vehicles):
        brand = random.choice(list(REAL_CAR_DATA.keys()))
        model = random.choice(REAL_CAR_DATA[brand])
        year = random.randint(2015, 2024)

        # 브랜드별 가격 범위 설정
        if brand in ['BMW', '벤츠', '아우디']:
            base_price = random.randint(2500, 8000)
        elif brand in ['현대', '기아']:
            base_price = random.randint(1200, 4000)
        elif brand in ['토요타', '혼다']:
            base_price = random.randint(1800, 5000)
        else:
            base_price = random.randint(1500, 3500)

        # 연식에 따른 가격 조정
        age_factor = max(0.6, 1 - (2024 - year) * 0.08)
        price = int(base_price * age_factor)

        # 주행거리 (연식에 따라)
        avg_yearly_km = random.randint(8000, 25000)
        mileage = (2024 - year) * avg_yearly_km + random.randint(-5000, 5000)
        mileage = max(0, mileage)

        # 연비 (차종별)
        if model in ['프리우스', 'i30', 'K3']:
            fuel_efficiency = random.uniform(12, 18)
        elif any(x in model.lower() for x in ['suv', 'santafe', 'sorento']):
            fuel_efficiency = random.uniform(8, 12)
        else:
            fuel_efficiency = random.uniform(9, 15)

        # 안전등급
        if brand in ['BMW', '벤츠', '아우디']:
            safety_rating = random.uniform(4.2, 5.0)
        else:
            safety_rating = random.uniform(3.5, 4.8)

        vehicle = {
            'vehicle_id': f'car_{i+1:03d}',
            'brand': brand,
            'model': model,
            'year': year,
            'price': price,
            'mileage': mileage,
            'fuel_type': random.choice(FUEL_TYPES),
            'body_type': random.choice(BODY_TYPES),
            'color': random.choice(COLORS),
            'location': random.choice(LOCATIONS),
            'fuel_efficiency': round(fuel_efficiency, 1),
            'safety_rating': round(safety_rating, 1),
            'engine_size': round(random.uniform(1.0, 3.5), 1),
            'transmission': random.choice(['auto', 'manual']),
            'accident_history': random.choice([0, 0, 0, 1, 1, 2]),  # 대부분 무사고
            'owner_count': random.randint(1, 3)
        }
        vehicles.append(vehicle)

    return pd.DataFrame(vehicles)

def generate_user_profiles(n_users=100):
    """다양한 사용자 프로필 생성"""
    users = []

    for i in range(n_users):
        age = random.randint(22, 65)

        # 연령대별 소득 분포
        if age < 30:
            income = random.randint(2800, 5500)
        elif age < 40:
            income = random.randint(3500, 7000)
        elif age < 50:
            income = random.randint(4000, 9000)
        else:
            income = random.randint(3500, 12000)

        # 선호도 패턴
        if age < 30:
            preferences = random.sample(['연비', '가격', '디자인', '브랜드', '성능'], 2)
        elif age < 40:
            preferences = random.sample(['안전성', '연비', '가족용', '공간', '브랜드'], 2)
        else:
            preferences = random.sample(['안전성', '편의성', '브랜드', '럭셔리', '신뢰성'], 2)

        user = {
            'user_id': f'user_{i+1:03d}',
            'age': age,
            'income': income,
            'gender': random.choice(['M', 'F']),
            'location': random.choice(LOCATIONS),
            'family_size': random.randint(1, 5),
            'preferences': preferences,
            'purpose': random.choice(['commute', 'family', 'business', 'leisure']),
            'budget_min': int(income * 0.5),
            'budget_max': int(income * 1.2)
        }
        users.append(user)

    return pd.DataFrame(users)

def generate_interactions(users_df, vehicles_df, n_interactions=2000):
    """사용자-차량 상호작용 데이터 생성"""
    interactions = []

    # 상호작용 타입별 선호도 점수
    interaction_scores = {
        'view': 0.3,
        'like': 0.7,
        'inquiry': 0.8,
        'favorite': 0.9,
        'purchase': 1.0
    }

    for _ in range(n_interactions):
        user = users_df.sample(1).iloc[0]
        vehicle = vehicles_df.sample(1).iloc[0]

        # 사용자 프로필에 따른 차량 선호도 계산
        preference_score = 0.5  # 기본 점수

        # 예산 맞춤
        if user['budget_min'] <= vehicle['price'] <= user['budget_max']:
            preference_score += 0.3
        elif vehicle['price'] > user['budget_max']:
            preference_score -= 0.4

        # 선호도 매칭
        if '연비' in user['preferences'] and vehicle['fuel_type'] in ['hybrid', 'electric']:
            preference_score += 0.2
        if '안전성' in user['preferences'] and vehicle['safety_rating'] >= 4.5:
            preference_score += 0.2
        if '브랜드' in user['preferences'] and vehicle['brand'] in ['BMW', '벤츠', '아우디']:
            preference_score += 0.2
        if '가격' in user['preferences'] and vehicle['price'] < user['budget_max'] * 0.8:
            preference_score += 0.2

        # 연령대별 브랜드 선호도
        if user['age'] < 35 and vehicle['brand'] in ['현대', '기아']:
            preference_score += 0.1
        elif user['age'] >= 40 and vehicle['brand'] in ['BMW', '벤츠', '아우디']:
            preference_score += 0.1

        # 선호도에 따른 상호작용 타입 결정
        preference_score = max(0.1, min(1.0, preference_score))

        if preference_score >= 0.8:
            interaction_type = random.choices(
                ['view', 'like', 'inquiry', 'favorite', 'purchase'],
                weights=[1, 3, 4, 3, 2]
            )[0]
        elif preference_score >= 0.6:
            interaction_type = random.choices(
                ['view', 'like', 'inquiry', 'favorite'],
                weights=[2, 4, 3, 1]
            )[0]
        else:
            interaction_type = random.choices(
                ['view', 'like'],
                weights=[7, 3]
            )[0]

        # 명시적 평점 (일부 상호작용에만)
        rating = None
        if random.random() < 0.3:  # 30% 확률로 평점 제공
            if preference_score >= 0.8:
                rating = random.choices([4, 5], weights=[3, 7])[0]
            elif preference_score >= 0.6:
                rating = random.choices([3, 4, 5], weights=[2, 5, 3])[0]
            else:
                rating = random.choices([1, 2, 3, 4], weights=[2, 3, 4, 1])[0]

        interaction = {
            'user_id': user['user_id'],
            'vehicle_id': vehicle['vehicle_id'],
            'interaction_type': interaction_type,
            'preference_score': interaction_scores[interaction_type],
            'rating': rating,
            'timestamp': datetime.now() - timedelta(days=random.randint(0, 365)),
            'session_id': f'session_{random.randint(1000, 9999)}',
            'implicit_feedback': preference_score
        }
        interactions.append(interaction)

    return pd.DataFrame(interactions)

def main():
    """메인 데이터 생성 함수"""
    print("차량 데이터셋 생성 중...")
    vehicles_df = generate_realistic_vehicle_dataset(200)
    print(f"{len(vehicles_df)}개 차량 데이터 생성 완료")

    print("사용자 프로필 생성 중...")
    users_df = generate_user_profiles(100)
    print(f"{len(users_df)}명 사용자 데이터 생성 완료")

    print("사용자-차량 상호작용 생성 중...")
    interactions_df = generate_interactions(users_df, vehicles_df, 2000)
    print(f"{len(interactions_df)}개 상호작용 데이터 생성 완료")

    # 데이터 저장
    vehicles_df.to_csv('ncf_vehicles.csv', index=False, encoding='utf-8')
    users_df.to_csv('ncf_users.csv', index=False, encoding='utf-8')
    interactions_df.to_csv('ncf_interactions.csv', index=False, encoding='utf-8')

    # 통계 출력
    print("\n데이터셋 통계:")
    print(f"차량 수: {len(vehicles_df)}")
    print(f"사용자 수: {len(users_df)}")
    print(f"상호작용 수: {len(interactions_df)}")
    print(f"평균 사용자당 상호작용: {len(interactions_df) / len(users_df):.1f}")
    print(f"평균 차량당 상호작용: {len(interactions_df) / len(vehicles_df):.1f}")
    print(f"스파시티: {1 - len(interactions_df) / (len(users_df) * len(vehicles_df)):.3f}")

    # 상호작용 타입별 분포
    print("\n상호작용 타입 분포:")
    print(interactions_df['interaction_type'].value_counts())

    # 브랜드별 분포
    print("\n브랜드별 차량 수:")
    print(vehicles_df['brand'].value_counts())

    print("\nNCF 데이터셋 생성 완료!")
    print("파일 저장: ncf_vehicles.csv, ncf_users.csv, ncf_interactions.csv")

if __name__ == "__main__":
    main()