import { useState, useEffect, useRef } from 'react';
import {
  Container,
  Box,
  Typography,
  LinearProgress,
  AppBar,
  Toolbar,
  IconButton
} from '@mui/material';
// @ts-ignore
import { Close, Logout, ArrowBack } from '@mui/icons-material';
import ChatBubble from './ChatBubble';
import ChatInput from './ChatInput';
import { apiClient } from '../services/apiClient';
import type { UserRegistration, UserPreferences } from '../services/apiClient';

// 챗봇 단계별 상태
type ChatStep = 'welcome' | 'signup' | 'preferences' | 'consultation';

// 메시지 타입
interface ChatMessage {
  id: string;
  type: 'user' | 'bot';
  message: string;
  timestamp: Date;
  options?: string[];
}

// 사용자 정보 타입 (백엔드 호환)
interface UserInfo {
  username?: string;
  email?: string;
  fullName?: string;
  full_name?: string;  // 백엔드 호환
  age?: number;
  phone?: string;
}

// 선호도 정보 타입 (백엔드 호환)
interface ChatBotPreferences {
  budgetMin?: number;
  budgetMax?: number;
  fuelType?: string;
  category?: string;
  transmission?: string;
  familySize?: number;
  usagePurpose?: string;
}

// Props 타입 정의
interface ChatBotContainerProps {
  onBackToLanding: () => void;
}

// 메인 ChatBot 컨테이너 구현
export default function ChatBotContainer({ onBackToLanding }: ChatBotContainerProps) {
  const [currentStep, setCurrentStep] = useState<ChatStep>('welcome');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [userInfo, setUserInfo] = useState<UserInfo>({});
  const [preferences, setPreferences] = useState<ChatBotPreferences>({});
  const [isTyping, setIsTyping] = useState(false);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 메시지 자동 스크롤
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 초기 웰컴 메시지
  useEffect(() => {
    addBotMessage(
      "안녕하세요! 🚗 CarFin AI 차량 추천 전문가입니다.\n\n" +
      "맞춤형 차량 추천과 금융 상담을 위해 간단한 정보를 수집하겠습니다.\n\n" +
      "시작하시겠어요?",
      ['네, 시작하겠습니다!', '더 알아보기']
    );
  }, []);

  // 진행률 계산
  const getProgressValue = () => {
    switch (currentStep) {
      case 'welcome': return 0;
      case 'signup': return 25;
      case 'preferences': return 50;
      case 'consultation': return 100;
      default: return 0;
    }
  };

  // 봇 메시지 추가 (타이핑 효과)
  const addBotMessage = (message: string, options?: string[]) => {
    setIsTyping(true);
    
    setTimeout(() => {
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        type: 'bot',
        message,
        timestamp: new Date(),
        options
      }]);
      setIsTyping(false);
    }, 1000 + Math.random() * 1000); // 1-2초 타이핑 시간
  };

  // 사용자 메시지 추가
  const addUserMessage = (message: string) => {
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      type: 'user',
      message,
      timestamp: new Date()
    }]);
  };

  // 메시지 처리 로직
  const handleMessage = (message: string) => {
    addUserMessage(message);
    handleUserResponse(message);
  };

  // 옵션 클릭 처리
  const handleOptionClick = (option: string) => {
    handleMessage(option);
  };

  // 사용자 응답 처리
  const handleUserResponse = (message: string) => {
    switch (currentStep) {
      case 'welcome':
        handleWelcomeResponse(message);
        break;
      case 'signup':
        handleSignupResponse(message);
        break;
      case 'preferences':
        handlePreferencesResponse(message);
        break;
      case 'consultation':
        handleConsultationResponse(message);
        break;
    }
  };

  // 웰컴 단계 응답 처리
  const handleWelcomeResponse = (message: string) => {
    if (message.includes('시작') || message.includes('네')) {
      setCurrentStep('signup');
        addBotMessage(
        "좋습니다! 먼저 회원가입을 진행하겠습니다.\n\n" +
        "성함을 알려주세요.",
        []
      );
    } else if (message.includes('알아보기')) {
      addBotMessage(
        "CarFin AI는 다음과 같은 서비스를 제공합니다:\n\n" +
        "🎯 AI 기반 맞춤 차량 추천\n" +
        "💳 금융 상품 비교 및 상담\n" +
        "📊 차량 가격 및 시장 분석\n\n" +
        "이제 시작해볼까요?",
        ['네, 시작하겠습니다!']
      );
    }
  };

  // 회원가입 단계 응답 처리
  const signupStep = userInfo.fullName ? 
    (userInfo.email ? 
      (userInfo.age ? 'phone' : 'age') 
      : 'email') 
    : 'fullName';

  const handleSignupResponse = (message: string) => {
    switch (signupStep) {
      case 'fullName':
        setUserInfo(prev => ({ ...prev, fullName: message }));
        addBotMessage(
          `${message}님, 반갑습니다! 이메일 주소를 알려주세요.`,
          []
        );
        break;
      
      case 'email':
        if (message.includes('@')) {
          setUserInfo(prev => ({ ...prev, email: message }));
          addBotMessage(
            "이메일이 등록되었습니다. 연령대를 알려주세요.",
            ['20대', '30대', '40대', '50대', '60대 이상']
          );
        } else {
          addBotMessage(
            "올바른 이메일 형식이 아닙니다. 다시 입력해주세요.\n(예: example@email.com)",
            []
          );
        }
        break;
      
      case 'age':
        const ageMatch = message.match(/\d+/);
        const ageGroup = ageMatch ? parseInt(ageMatch[0]) : 
          (message.includes('20대') ? 25 :
           message.includes('30대') ? 35 :
           message.includes('40대') ? 45 :
           message.includes('50대') ? 55 : 65);
        
        setUserInfo(prev => ({ ...prev, age: ageGroup }));
        addBotMessage(
          "연락처를 입력해주세요. (선택사항)",
          ['건너뛰기']
        );
        break;
      
      case 'phone':
        if (message === '건너뛰기') {
          completeSignup();
        } else {
          setUserInfo(prev => ({ ...prev, phone: message }));
          completeSignup();
        }
        break;
    }
  };

  // 회원가입 완료 (실제 API 호출)
  const completeSignup = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // 백엔드에 사용자 등록
      const registrationData: UserRegistration = {
        full_name: userInfo.fullName || userInfo.full_name || '',
        email: userInfo.email || '',
        age: userInfo.age || 25,
        phone: userInfo.phone
      };

      const response = await apiClient.registerUser(registrationData);
      
      if (response.status === 'success') {
        // 사용자 ID 저장
        setCurrentUserId(response.user_id);
        
        // 다음 단계로 진행
        setCurrentStep('preferences');
        addBotMessage(
          `${userInfo.fullName}님의 정보가 등록되었습니다! 🎉\n\n` +
          "이제 차량 선호도를 파악하기 위한 간단한 테스트를 진행하겠습니다.\n\n" +
          "예산 범위를 알려주세요.",
          ['1000만원 이하', '1000-3000만원', '3000-5000만원', '5000만원 이상']
        );
      } else {
        throw new Error('회원가입에 실패했습니다');
      }
    } catch (error) {
      console.error('Registration failed:', error);
      setError(error instanceof Error ? error.message : '회원가입 중 오류가 발생했습니다');
      addBotMessage(
        "죄송합니다. 회원가입 중 오류가 발생했습니다.\n\n다시 시도해주세요.",
        ['다시 시도']
      );
    } finally {
      setIsLoading(false);
    }
  };

  // 선호도 테스트 응답 처리
  const preferencesStep = preferences.budgetMin !== undefined ? 
    (preferences.fuelType ? 
      (preferences.category ? 
        (preferences.familySize !== undefined ? 'complete' : 'familySize')
        : 'category') 
      : 'fuelType') 
    : 'budget';

  const handlePreferencesResponse = (message: string) => {
    switch (preferencesStep) {
      case 'budget':
        let budgetMin = 0, budgetMax = 0;
        if (message.includes('1000만원 이하')) {
          budgetMin = 0; budgetMax = 1000;
        } else if (message.includes('1000-3000')) {
          budgetMin = 1000; budgetMax = 3000;
        } else if (message.includes('3000-5000')) {
          budgetMin = 3000; budgetMax = 5000;
        } else if (message.includes('5000만원 이상')) {
          budgetMin = 5000; budgetMax = 10000;
        }
        
        setPreferences(prev => ({ ...prev, budgetMin, budgetMax }));
        addBotMessage(
          "선호하는 연료 타입을 선택해주세요.",
          ['가솔린', '디젤', '하이브리드', '전기차', '상관없음']
        );
        break;
      
      case 'fuelType':
        setPreferences(prev => ({ ...prev, fuelType: message }));
        addBotMessage(
          "어떤 종류의 차량을 선호하시나요?",
          ['소형차', '중형차', '대형차', 'SUV', '상관없음']
        );
        break;
      
      case 'category':
        setPreferences(prev => ({ ...prev, category: message }));
        addBotMessage(
          "가족 구성원 수를 알려주세요.",
          ['1-2명', '3-4명', '5명 이상']
        );
        break;
      
      case 'familySize':
        const familySize = message.includes('1-2') ? 2 : 
                          message.includes('3-4') ? 4 : 6;
        setPreferences(prev => ({ ...prev, familySize }));
        completePreferences();
        break;
    }
  };

  // 선호도 테스트 완료 (실제 API 호출)
  const completePreferences = async () => {
    try {
      setIsLoading(true);
      setError(null);

      if (!currentUserId) {
        throw new Error('사용자 정보가 없습니다. 다시 로그인해주세요.');
      }

      // 백엔드에 선호도 저장
      const preferencesData: Omit<UserPreferences, 'user_id'> = {
        budget_min: preferences.budgetMin,
        budget_max: preferences.budgetMax,
        fuel_type: preferences.fuelType,
        category: preferences.category,
        transmission: preferences.transmission,
        family_size: preferences.familySize,
        usage_purpose: preferences.usagePurpose
      };

      const response = await apiClient.saveUserPreferences(currentUserId, preferencesData);
      
      if (response.status === 'success') {
        // 다음 단계로 진행
        setCurrentStep('consultation');
        addBotMessage(
          "선호도 분석이 완료되었습니다! 🎯\n\n" +
          "이제 AI 전문가가 맞춤형 차량을 추천해드리겠습니다.\n\n" +
          "어떤 도움이 필요하신가요?",
          ['차량 추천 받기', '금융 상담', '시장 분석']
        );
      } else {
        throw new Error('선호도 저장에 실패했습니다');
      }
    } catch (error) {
      console.error('Preferences save failed:', error);
      setError(error instanceof Error ? error.message : '선호도 저장 중 오류가 발생했습니다');
      addBotMessage(
        "죄송합니다. 선호도 저장 중 오류가 발생했습니다.\n\n다시 시도해주세요.",
        ['다시 시도']
      );
    } finally {
      setIsLoading(false);
    }
  };

  // 상담 응답 처리 (실제 AI 에이전트 연동)
  const handleConsultationResponse = async (message: string) => {
    try {
      setIsLoading(true);
      setError(null);

      if (!currentUserId) {
        throw new Error('사용자 정보가 없습니다. 다시 로그인해주세요.');
      }

      // 사용자 메시지를 UI에 추가
      addUserMessage(message);

      // 타이핑 표시
      setIsTyping(true);

      // AI 에이전트에게 채팅 메시지 전송
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
      
      if (response.status === 'success') {
        // AI 응답 표시
        setIsTyping(false);
        addBotMessage(
          response.response,
          ['다른 차량 추천 받기', '금융 상담 요청', '더 자세한 정보']
        );

        // ML 추천 결과가 있다면 추가 정보 표시
        if (response.ml_recommendations && response.ml_recommendations.length > 0) {
          setTimeout(() => {
            addBotMessage(
              "🚗 추천 차량 목록을 확인하시겠어요?\n\n" +
              "상세한 금융 상담도 가능합니다!",
              ['추천 차량 보기', '금융 옵션 비교', '다른 조건으로 다시 검색']
            );
          }, 2000);
        }
      } else {
        throw new Error('AI 상담 중 문제가 발생했습니다');
      }
    } catch (error) {
      console.error('AI consultation failed:', error);
      setIsTyping(false);
      setError(error instanceof Error ? error.message : 'AI 상담 중 오류가 발생했습니다');
      addBotMessage(
        "죄송합니다. 일시적인 문제가 발생했습니다.\n\n" +
        "잠시 후 다시 시도해주시거나 다른 질문을 해주세요.",
        ['다시 시도', '다른 질문하기']
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Container maxWidth="md" sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* 헤더 */}
      <AppBar position="static" elevation={0}>
        <Toolbar>
          <IconButton color="inherit" onClick={onBackToLanding} sx={{ mr: 2 }}>
            <ArrowBack />
          </IconButton>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            🚗 CarFin AI 상담사
          </Typography>
          <IconButton color="inherit">
            <Logout />
          </IconButton>
        </Toolbar>
      </AppBar>

      {/* 진행률 표시 */}
      <Box sx={{ p: 2 }}>
        <LinearProgress 
          variant="determinate" 
          value={getProgressValue()} 
          sx={{ height: 8, borderRadius: 4 }}
        />
        <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
          {currentStep === 'welcome' && '시작하기'}
          {currentStep === 'signup' && '회원가입 진행 중'}
          {currentStep === 'preferences' && '선호도 테스트 진행 중'}
          {currentStep === 'consultation' && '상담 진행 중'}
        </Typography>
      </Box>

      {/* 채팅 영역 */}
      <Box 
        sx={{ 
          flex: 1, 
          overflowY: 'auto', 
          p: 2,
          backgroundColor: '#f8f9fa'
        }}
      >
        {messages.map((msg) => (
          <ChatBubble
            key={msg.id}
            message={msg.message}
            type={msg.type}
            timestamp={msg.timestamp}
            options={msg.options}
            onOptionClick={handleOptionClick}
          />
        ))}
        
        {/* 타이핑 표시 */}
        {isTyping && (
          <ChatBubble
            message=""
            type="bot"
            showTyping={true}
          />
        )}
        
        <div ref={messagesEndRef} />
      </Box>

      {/* 입력 영역 */}
      <ChatInput
        onSendMessage={handleMessage}
        disabled={isTyping}
        placeholder={
          currentStep === 'welcome' ? "안녕하세요!" :
          currentStep === 'signup' ? "정보를 입력해주세요..." :
          currentStep === 'preferences' ? "선호도를 알려주세요..." :
          "궁금한 점을 질문해주세요..."
        }
      />
    </Container>
  );
}