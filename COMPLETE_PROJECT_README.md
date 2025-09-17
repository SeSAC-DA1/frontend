# CarFin AI: 완전한 멀티에이전트 차량 추천 및 금융 상담 시스템

## 🚗 프로젝트 개요

CarFin은 **CrewAI 기반 멀티에이전트 시스템**과 **PyCaret 머신러닝**을 결합한 차세대 AI 차량 추천 및 금융 상담 플랫폼입니다. 

**핵심 가치 제안:**
- 🤖 **2개 전문 AI 에이전트 협업**: 차량 추천 전문가 + 금융 상담 전문가
- 🧠 **PyCaret ML 개인화 추천**: 협업 필터링 기반 정확한 차량 매칭
- 💬 **하이브리드 UI**: 빠른 드롭다운 입력 + 자연스러운 AI 채팅
- 📊 **실시간 분석**: 사용자 프로필 → ML 분석 → 맞춤 추천 → 금융 옵션 계산

---

## 🏗️ 시스템 아키텍처

### 전체 구조도
```
┌─────────────────┐    ┌───────────────────┐    ┌─────────────────┐
│   Frontend      │    │     Backend       │    │   AI Agents     │
│                 │    │                   │    │                 │
│ React + TS      │◄──►│   FastAPI         │◄──►│ CrewAI + GPT-5  │
│ Material-UI     │    │   Port 8000       │    │ Multi-Agent     │
│ Port 5000       │    │                   │    │                 │
└─────────────────┘    └───────────────────┘    └─────────────────┘
         │                        │                        │
         │                        ▼                        ▼
         │              ┌───────────────────┐    ┌─────────────────┐
         │              │   PostgreSQL      │    │  PyCaret ML     │
         │              │   Database        │    │  Recommendation │
         │              │                   │    │  Engine         │
         └──────────────►│ User Data        │    │                 │
                        │ Vehicle Data      │    │ Collaborative   │
                        │ Preferences       │    │ Filtering       │
                        └───────────────────┘    └─────────────────┘
```

### 데이터 플로우
```
사용자 입력 → 구조화된 프로필 → ML 분석 → AI 에이전트 처리 → 개인화 추천 + 금융 옵션
```

---

## 📁 프로젝트 구조

```
CarFin/
├── 📂 backend/
│   ├── simple_main.py              # FastAPI 메인 서버
│   └── pyproject.toml              # Python 의존성
├── 📂 agents/
│   └── crew_setup.py               # CrewAI 멀티에이전트 시스템
├── 📂 ml/
│   └── recommendation_engine.py    # PyCaret ML 추천 엔진
├── 📂 data/
│   ├── encar_crawler.py           # 엔카 데이터 크롤러
│   ├── encar_sample_data.py       # 샘플 데이터 생성
│   └── aws_encar_crawler.py       # AWS 기반 크롤러
├── 📂 frontend/
│   ├── 📂 src/
│   │   ├── 📂 components/          # React 컴포넌트들
│   │   │   ├── HybridCarFinInterface.tsx    # 메인 하이브리드 UI
│   │   │   ├── ChatBotContainer.tsx         # AI 채팅 컨테이너
│   │   │   ├── ChatBubble.tsx              # 채팅 말풍선
│   │   │   ├── GuidedInputPanel.tsx        # 빠른 입력 패널
│   │   │   └── EnhancedCarCard.tsx         # 차량 카드 컴포넌트
│   │   ├── 📂 services/
│   │   │   └── apiClient.ts               # API 통신 클라이언트
│   │   ├── App.tsx                        # 메인 앱 컴포넌트
│   │   └── main.tsx                       # 앱 진입점
│   ├── package.json                       # Node.js 의존성
│   ├── vite.config.ts                     # Vite 빌드 설정
│   └── tsconfig.json                      # TypeScript 설정
└── replit.md                              # 프로젝트 메모리
```

---

## 🔧 백엔드 시스템 상세

### 1. FastAPI 서버 (simple_main.py)

**주요 기능:**
- 멀티에이전트 시스템과 연동된 RESTful API
- 사용자 관리, 선호도 저장, 실시간 채팅
- CORS 설정으로 프론트엔드와 통신

**핵심 API 엔드포인트:**
```python
# 기본 상태 확인
GET /                           # 서버 상태
GET /health                     # 상세 헬스체크

# 사용자 관리
POST /api/users/register        # 사용자 등록
POST /api/users/{user_id}/preferences  # 선호도 저장
GET /api/users/{user_id}        # 사용자 정보 조회

# AI 상담 및 추천
POST /api/chat                  # 멀티에이전트 채팅 상담
POST /api/recommend             # 차량 추천 요청
POST /api/finance               # 금융 옵션 계산

# 차량 정보
GET /api/cars/{car_id}          # 특정 차량 상세 정보
GET /api/users/{user_id}/conversations  # 대화 기록
```

**데이터 모델:**
```python
# 사용자 등록
class UserRegistration(BaseModel):
    full_name: str
    email: str
    age: int
    phone: Optional[str]

# 사용자 선호도
class UserPreferences(BaseModel):
    user_id: str
    budget_min: Optional[int]
    budget_max: Optional[int]
    fuel_type: Optional[str]      # "Gasoline", "Hybrid", "Electric"
    category: Optional[str]       # "Compact", "Mid-size", "SUV", "Luxury"
    transmission: Optional[str]
    family_size: Optional[int]
    usage_purpose: Optional[str]

# 채팅 메시지
class ChatMessage(BaseModel):
    user_id: str
    message: str
    context: Optional[Dict[str, Any]]
```

**환경 변수:**
```bash
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=postgresql://user:password@host:port/database
```

### 2. CrewAI 멀티에이전트 시스템 (agents/crew_setup.py)

**시스템 구성:**
```python
class CarFinAgents:
    def __init__(self):
        self.vehicle_agent = Agent(...)      # 차량 추천 전문가
        self.finance_agent = Agent(...)      # 금융 상담 전문가
        self.recommendation_engine = CarRecommendationEngine()
```

**에이전트 1: 차량 추천 전문가**
- **역할**: 사용자 요구사항 분석 → PyCaret ML 추천 → 친근한 설명
- **목표**: 최적의 차량 3개 추천 및 이해하기 쉬운 설명
- **특화**: 20-30대 첫차 구매자 심리 이해, 기술용어 지양

**에이전트 2: 금융 상담 전문가**
- **역할**: 대출/리스/할부 옵션 계산 및 맞춤 추천
- **목표**: 월 납부액, 총비용, 장단점 명확 비교
- **특화**: 복잡한 금융 계산을 실생활 언어로 설명

**GPT-5 통합:**
```python
# 사용자 요구사항 구조화
def _parse_user_requirements(self, user_message: str) -> Dict[str, Any]:
    response = openai_client.chat.completions.create(
        model="gpt-5",
        messages=[{"role": "user", "content": parse_prompt}],
        response_format={"type": "json_object"}
    )
```

**워크플로우:**
1. 사용자 메시지 → GPT-5로 구조화된 프로필 생성
2. 구조화된 프로필 → PyCaret ML 추천 실행
3. ML 결과 → 차량 추천 에이전트가 친근한 설명 생성
4. 선택된 차량 → 금융 상담 에이전트가 옵션 계산

### 3. PyCaret ML 추천 엔진 (ml/recommendation_engine.py)

**핵심 기능:**
```python
class CarRecommendationEngine:
    def __init__(self):
        self.model = None
        self.data = None
        self.engine = None  # PostgreSQL 연결
        
    def load_data(self) -> bool:
        # PostgreSQL에서 차량 데이터 로드
        
    def train_model(self) -> bool:
        # PyCaret로 협업 필터링 모델 훈련
        
    def get_recommendations(self, user_profile: Dict, n_recommendations: int = 3):
        # 개인화 추천 생성
```

**추천 알고리즘:**
- **협업 필터링**: 유사한 사용자들의 선호도 기반 추천
- **컨텐츠 기반 필터링**: 차량 특성 매칭 (백업 알고리즘)
- **하이브리드 접근**: 두 방법의 조합으로 정확도 향상

**데이터 전처리:**
- 사용자 프로필 정규화
- 차량 특성 벡터화
- 결측값 처리 및 스케일링

### 4. 데이터베이스 스키마

**PostgreSQL 테이블 구조:**
```sql
-- 사용자 테이블
CREATE TABLE users (
    user_id VARCHAR PRIMARY KEY,
    full_name VARCHAR NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    age INTEGER,
    phone VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 사용자 선호도 (JSONB로 유연성 확보)
CREATE TABLE user_preferences (
    user_id VARCHAR REFERENCES users(user_id),
    preferences JSONB,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 차량 데이터
CREATE TABLE vehicles (
    car_id SERIAL PRIMARY KEY,
    make VARCHAR,
    model VARCHAR,
    year INTEGER,
    price INTEGER,
    fuel_type VARCHAR,
    category VARCHAR,
    transmission VARCHAR,
    features JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 대화 기록
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR REFERENCES users(user_id),
    message TEXT,
    response TEXT,
    ml_data JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

---

## 🎨 프론트엔드 시스템 상세

### 1. 기술 스택
```json
{
  "framework": "React 19.1.1",
  "language": "TypeScript",
  "build": "Vite 7.1.5",
  "ui": "Material-UI (MUI) 7.3.2",
  "state": "React Hooks",
  "api": "Fetch API"
}
```

### 2. 메인 컴포넌트 (HybridCarFinInterface.tsx)

**하이브리드 UI 설계:**
```typescript
// 왼쪽: 빠른 입력 패널 | 오른쪽: 실시간 결과
<Grid container spacing={3}>
  <Grid size={6}>
    <GuidedInputPanel />      // 드롭다운 빠른 입력
    <ChatBotContainer />      // AI 채팅 인터페이스
  </Grid>
  <Grid size={6}>
    <RecommendationResults /> // 실시간 추천 결과
    <CarCards />             // 차량 카드들
  </Grid>
</Grid>
```

**상태 관리:**
```typescript
const [currentStep, setCurrentStep] = useState<'welcome' | 'signup' | 'preferences' | 'consultation'>('welcome');
const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
const [preferences, setPreferences] = useState<UserPreferences>({});
const [recommendations, setRecommendations] = useState<CarRecommendation[]>([]);
const [messages, setMessages] = useState<ChatMessage[]>([]);
```

### 3. AI 채팅 컨테이너 (ChatBotContainer.tsx)

**실시간 채팅 기능:**
```typescript
const handleChatMessage = async (message: string) => {
  // 사용자 메시지 추가
  addUserMessage(message);
  
  // 타이핑 표시
  setIsTyping(true);
  
  // AI 에이전트에게 전송
  const chatData = {
    user_id: currentUserId,
    message: message,
    context: {
      step: 'consultation',
      preferences: preferences,
      user_info: userInfo
    }
  };
  
  const response = await apiClient.sendChatMessage(chatData);
  
  // AI 응답 처리
  if (response.status === 'success') {
    setIsTyping(false);
    addBotMessage(response.response, response.options);
    
    // ML 추천 결과 업데이트
    if (response.ml_recommendations) {
      updateRecommendations(response.ml_recommendations);
    }
  }
};
```

**채팅 말풍선 (ChatBubble.tsx):**
- 사용자/AI 구분된 디자인
- 타이핑 애니메이션
- 옵션 버튼 지원
- 타임스탬프 표시

### 4. 빠른 입력 패널 (GuidedInputPanel.tsx)

**드롭다운 기반 빠른 설정:**
```typescript
// 예산 범위
<FormControl fullWidth>
  <InputLabel>예산 범위</InputLabel>
  <Select value={budget} onChange={handleBudgetChange}>
    <MenuItem value="1000-2000">1,000만원 - 2,000만원</MenuItem>
    <MenuItem value="2000-3000">2,000만원 - 3,000만원</MenuItem>
    <MenuItem value="3000-4000">3,000만원 - 4,000만원</MenuItem>
    <MenuItem value="4000+">4,000만원 이상</MenuItem>
  </Select>
</FormControl>

// 연료 타입
<ToggleButtonGroup value={fuelType} exclusive onChange={handleFuelChange}>
  <ToggleButton value="gasoline">가솔린</ToggleButton>
  <ToggleButton value="hybrid">하이브리드</ToggleButton>
  <ToggleButton value="electric">전기차</ToggleButton>
</ToggleButtonGroup>
```

### 5. API 클라이언트 (apiClient.ts)

**타입 안전한 API 통신:**
```typescript
class CarFinAPIClient {
  private baseURL = 'http://localhost:8000';
  
  // 사용자 등록
  async registerUser(userData: UserRegistration): Promise<RegisterResponse> {
    return this.post<RegisterResponse>('/api/users/register', userData);
  }
  
  // AI 채팅
  async sendChatMessage(chatData: ChatMessage): Promise<ChatResponse> {
    return this.post<ChatResponse>('/api/chat', chatData);
  }
  
  // 차량 추천
  async getRecommendations(request: RecommendationRequest): Promise<RecommendationResponse> {
    return this.post<RecommendationResponse>('/api/recommend', request);
  }
  
  private async post<T>(endpoint: string, data: any): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  }
}
```

---

## 🚀 설치 및 실행 가이드

### 1. 시스템 요구사항
```
- Python 3.11+
- Node.js 20+
- PostgreSQL 13+
- 8GB+ RAM (PyCaret ML 모델 훈련용)
```

### 2. 환경 설정

**Step 1: 저장소 클론**
```bash
git clone https://github.com/yourusername/carfin-ai.git
cd carfin-ai
```

**Step 2: 환경 변수 설정**
```bash
# .env 파일 생성
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/carfin_db
PGHOST=localhost
PGPORT=5432
PGUSER=your_db_user
PGPASSWORD=your_db_password
PGDATABASE=carfin_db
```

**Step 3: PostgreSQL 데이터베이스 설정**
```sql
-- 데이터베이스 생성
CREATE DATABASE carfin_db;

-- 사용자 생성 (필요시)
CREATE USER carfin_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE carfin_db TO carfin_user;
```

### 3. 백엔드 설치 및 실행

**Python 의존성 설치:**
```bash
# uv 패키지 매니저 사용 (추천)
uv sync

# 또는 pip 사용
pip install -r requirements.txt
```

**백엔드 서버 실행:**
```bash
# 메인 디렉토리에서
python simple_main.py

# 또는 특정 포트로 실행
uvicorn simple_main:app --host 0.0.0.0 --port 8000 --reload
```

**백엔드 확인:**
```bash
# 헬스체크
curl http://localhost:8000/health

# API 문서 (자동 생성)
# 브라우저에서 http://localhost:8000/docs 접속
```

### 4. 프론트엔드 설치 및 실행

**Node.js 의존성 설치:**
```bash
cd frontend
npm install
```

**개발 서버 실행:**
```bash
npm run dev

# Vite 서버가 http://localhost:5000 에서 실행됩니다
```

**빌드 (프로덕션):**
```bash
npm run build
npm run preview
```

### 5. 전체 시스템 실행 순서

```bash
# Terminal 1: 백엔드
python simple_main.py

# Terminal 2: 프론트엔드
cd frontend && npm run dev

# Terminal 3: 데이터베이스 (필요시)
pg_ctl start -D /your/postgres/data/path
```

**확인 체크리스트:**
- ✅ 백엔드: http://localhost:8000/health
- ✅ 프론트엔드: http://localhost:5000
- ✅ API 문서: http://localhost:8000/docs
- ✅ 데이터베이스 연결 확인

---

## 🔍 핵심 기능 사용 가이드

### 1. 사용자 등록 플로우
```
웰컴 화면 → 사용자 정보 입력 → 선호도 설정 → AI 상담 시작
```

### 2. AI 멀티에이전트 상담
```
사용자: "가족용 차량 추천해주세요. 예산은 3천만원입니다."
    ↓
GPT-5: 사용자 요구사항 구조화
    ↓
PyCaret ML: 개인화 추천 분석
    ↓
차량 추천 에이전트: "고객님께 추천하는 차량 3대입니다..."
    ↓
사용자: "두 번째 차량의 금융 옵션이 궁금해요."
    ↓
금융 상담 에이전트: "해당 차량의 금융 옵션을 분석해드리겠습니다..."
```

### 3. 하이브리드 UI 활용
- **빠른 추천**: 왼쪽 드롭다운으로 즉시 설정
- **상세 상담**: AI 채팅으로 자연스러운 대화
- **실시간 결과**: 오른쪽에서 즉시 추천 확인

---

## 🧪 테스트 및 디버깅

### 1. API 테스트
```bash
# 사용자 등록 테스트
curl -X POST http://localhost:8000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "김철수",
    "email": "test@example.com",
    "age": 28
  }'

# AI 채팅 테스트
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_id_here",
    "message": "가족용 차량 추천해주세요",
    "context": {}
  }'
```

### 2. 일반적인 문제 해결

**문제: AI 에이전트 응답 없음**
```bash
# 해결: OpenAI API 키 확인
echo $OPENAI_API_KEY

# 로그 확인
tail -f logs/carfin_backend.log
```

**문제: ML 추천 오류**
```python
# 해결: PyCaret 모델 재훈련
from ml.recommendation_engine import CarRecommendationEngine
engine = CarRecommendationEngine()
engine.load_data()
engine.train_model()
```

**문제: 프론트엔드 API 연결 실패**
```typescript
// 해결: API 클라이언트 baseURL 확인
const baseURL = 'http://localhost:8000';  // 백엔드 포트 확인
```

### 3. 로그 및 모니터링
```bash
# 백엔드 로그
tail -f logs/uvicorn.log

# 프론트엔드 개발자 도구
# 브라우저 F12 → Console 탭

# 데이터베이스 로그
tail -f /var/log/postgresql/postgresql.log
```

---

## 📈 확장 및 개선 방안

### 1. 성능 최적화
- **Redis 캐싱**: 추천 결과 캐싱으로 응답 속도 향상
- **비동기 처리**: Celery로 ML 훈련 백그라운드 처리
- **CDN 적용**: 정적 파일 배포 최적화

### 2. 추가 기능
- **음성 인터페이스**: Speech-to-Text API 통합
- **이미지 검색**: 차량 이미지 기반 유사 차량 검색
- **금융사 연동**: 실시간 대출 승인 API 연계

### 3. 배포 환경
```yaml
# docker-compose.yml 예시
version: '3.8'
services:
  backend:
    build: .
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/carfin
  
  frontend:
    build: ./frontend
    ports: ["5000:5000"]
  
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: carfin
      POSTGRES_PASSWORD: password
```

---

## 👥 개발팀 가이드

### 1. 코드 컨벤션
```python
# Python (Black 포매터 사용)
def get_user_recommendations(user_id: str) -> List[CarRecommendation]:
    """사용자별 차량 추천을 가져옵니다."""
    pass
```

```typescript
// TypeScript (ESLint + Prettier)
interface UserPreferences {
  budgetMin?: number;
  budgetMax?: number;
  fuelType?: 'gasoline' | 'hybrid' | 'electric';
}
```

### 2. Git 워크플로우
```bash
# 기능 개발
git checkout -b feature/new-ml-algorithm
git commit -m "feat: 새로운 ML 알고리즘 구현"
git push origin feature/new-ml-algorithm

# PR 생성 후 리뷰
# 메인 브랜치 머지
```

### 3. 테스트 전략
```python
# 백엔드 테스트
pytest tests/test_agents.py
pytest tests/test_ml_engine.py

# 프론트엔드 테스트
npm test
npm run test:coverage
```

---

## 📞 지원 및 문의

### 문제 해결 순서
1. **로그 확인**: 백엔드/프론트엔드 로그 분석
2. **API 테스트**: curl 또는 Postman으로 API 직접 테스트
3. **데이터베이스 확인**: PostgreSQL 연결 및 데이터 검증
4. **의존성 확인**: Python/Node.js 패키지 버전 검증

### 주요 설정 파일
- `pyproject.toml`: Python 의존성
- `package.json`: Node.js 의존성
- `vite.config.ts`: 프론트엔드 빌드 설정
- `.env`: 환경 변수

### 개발 도구
- **API 문서**: http://localhost:8000/docs (FastAPI 자동 생성)
- **데이터베이스 GUI**: pgAdmin 또는 DBeaver
- **로그 뷰어**: tail, journalctl 또는 GUI 도구

---

**🎯 이 README를 따라하면 다른 에이전트도 CarFin AI 시스템을 완전히 이해하고 실행할 수 있습니다!** 

**마지막 업데이트**: 2025년 9월 16일  
**개발자**: AI Agent  
**기술 스택**: Python, React, CrewAI, PyCaret, OpenAI GPT-5, PostgreSQL