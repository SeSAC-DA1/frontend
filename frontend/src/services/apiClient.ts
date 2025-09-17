/**
 * CarFin API Client
 * 백엔드 API와의 통신을 담당하는 서비스
 */

// 백엔드 API Base URL (Replit 환경용)
// Replit 환경에서는 상대 경로 사용 (자동 프록시 처리)
const API_BASE_URL = '';

// 사용자 등록 데이터 타입
interface UserRegistration {
  full_name: string;
  email: string;
  age: number;
  phone?: string;
}

// 사용자 선호도 데이터 타입
interface UserPreferences {
  user_id: string;
  budget_min?: number;
  budget_max?: number;
  fuel_type?: string;
  category?: string;
  transmission?: string;
  family_size?: number;
  usage_purpose?: string;
}

// 채팅 메시지 타입
interface ChatMessage {
  user_id: string;
  message: string;
  context?: Record<string, any>;
}

// API 응답 기본 타입
interface ApiResponse<T = any> {
  status: string;
  message?: string;
  data?: T;
}

// 사용자 등록 응답 타입
interface UserRegistrationResponse {
  status: string;
  message: string;
  user_id: string;
  user_data: {
    user_id: string;
    full_name: string;
    email: string;
    age: number;
    phone?: string;
    created_at: string;
  };
}

// 채팅 응답 타입
interface ChatResponse {
  status: string;
  response: string;
  ml_recommendations: any[];
  conversation_id: number;
}

class CarFinAPIClient {
  private baseURL: string;

  constructor() {
    this.baseURL = API_BASE_URL;
  }

  // HTTP 요청 헬퍼
  private async makeRequest<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    const response = await fetch(url, { ...defaultOptions, ...options });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP Error: ${response.status}`);
    }

    return response.json();
  }

  // GET 요청
  async get<T>(endpoint: string): Promise<T> {
    return this.makeRequest<T>(endpoint, { method: 'GET' });
  }

  // POST 요청
  async post<T>(endpoint: string, data: any): Promise<T> {
    return this.makeRequest<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // 사용자 등록
  async registerUser(userData: UserRegistration): Promise<UserRegistrationResponse> {
    return this.post<UserRegistrationResponse>('/api/users/register', userData);
  }

  // 사용자 정보 조회
  async getUserInfo(userId: string): Promise<ApiResponse> {
    return this.get<ApiResponse>(`/api/users/${userId}`);
  }

  // 사용자 선호도 저장
  async saveUserPreferences(userId: string, preferences: Omit<UserPreferences, 'user_id'>): Promise<ApiResponse> {
    const fullPreferences = { user_id: userId, ...preferences };
    return this.post<ApiResponse>(`/api/users/${userId}/preferences`, fullPreferences);
  }

  // AI 채팅 상담
  async sendChatMessage(chatData: ChatMessage): Promise<ChatResponse> {
    return this.post<ChatResponse>('/api/chat', chatData);
  }

  // 대화 기록 조회
  async getConversationHistory(userId: string): Promise<ApiResponse> {
    return this.get<ApiResponse>(`/api/users/${userId}/conversations`);
  }

  // 차량 추천 (기존 API)
  async getCarRecommendations(message: string, userId?: string): Promise<ApiResponse> {
    return this.post<ApiResponse>('/api/recommend', { 
      message, 
      user_id: userId 
    });
  }

  // 금융 상담 (기존 API)
  async getFinanceConsultation(carId: string, budget: number): Promise<ApiResponse> {
    return this.post<ApiResponse>('/api/finance', { 
      car_id: carId, 
      user_budget: budget 
    });
  }

  // 차량 목록 조회
  async getCarList(category?: string, maxPrice?: number): Promise<ApiResponse> {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (maxPrice) params.append('max_price', maxPrice.toString());
    
    const queryString = params.toString();
    return this.get<ApiResponse>(`/api/cars${queryString ? '?' + queryString : ''}`);
  }

  // 특정 차량 정보 조회
  async getCarDetails(carId: number): Promise<ApiResponse> {
    return this.get<ApiResponse>(`/api/cars/${carId}`);
  }

  // 헬스 체크
  async healthCheck(): Promise<ApiResponse> {
    return this.get<ApiResponse>('/health');
  }
}

// 싱글톤 인스턴스 생성
export const apiClient = new CarFinAPIClient();

// 타입들도 export
export type {
  UserRegistration,
  UserPreferences,
  ChatMessage,
  ApiResponse,
  UserRegistrationResponse,
  ChatResponse
};