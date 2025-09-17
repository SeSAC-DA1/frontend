import { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Grid,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Card,
  CardContent,
  Chip,
  AppBar,
  Toolbar,
  Tabs,
  Tab,
  Alert
} from '@mui/material';
import ChatBubble from './ChatBubble';
import ChatInput from './ChatInput';
import { apiClient } from '../services/apiClient';
import type { UserRegistration, UserPreferences } from '../services/apiClient';

// 탭 패널 컴포넌트
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel({ children, value, index }: TabPanelProps) {
  return (
    <div hidden={value !== index} style={{ height: '100%' }}>
      {value === index && <Box sx={{ p: 3, height: '100%' }}>{children}</Box>}
    </div>
  );
}

// 메시지 타입
interface ChatMessage {
  id: string;
  type: 'user' | 'bot';
  message: string;
  timestamp: Date;
  options?: string[];
}

// 추천 결과 타입
interface RecommendationResult {
  car_id: number;
  make: string;
  model: string;
  year: number;
  price: number;
  fuel_type: string;
  category: string;
  description: string;
  recommendation_reason: string;
}

export default function HybridCarFinInterface() {
  const [activeTab, setActiveTab] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // 빠른 입력 폼 상태
  const [quickForm, setQuickForm] = useState({
    name: '',
    age: '',
    budget: '',
    fuelType: '',
    category: '',
    familySize: '',
    purpose: ''
  });

  // 챗봇 상태
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  
  // 추천 결과 상태
  const [recommendations, setRecommendations] = useState<RecommendationResult[]>([]);
  const [aiResponse, setAiResponse] = useState('');

  // 초기 메시지
  useEffect(() => {
    addBotMessage(
      "안녕하세요! 🚗 CarFin AI 입니다.\n\n" +
      "두 가지 방법으로 맞춤형 차량을 추천해드릴 수 있습니다:\n\n" +
      "1️⃣ **빠른 추천**: 왼쪽 폼을 채워주세요\n" +
      "2️⃣ **AI 상담**: 저와 자유롭게 대화해보세요\n\n" +
      "어떤 방법을 선호하시나요?",
      ['빠른 추천', 'AI 상담', '둘 다 써보기']
    );
  }, []);

  const addBotMessage = (message: string, options?: string[]) => {
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      type: 'bot',
      message,
      timestamp: new Date(),
      options
    }]);
  };

  const addUserMessage = (message: string) => {
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      type: 'user',
      message,
      timestamp: new Date()
    }]);
  };

  // 빠른 추천 제출
  const handleQuickRecommendation = async () => {
    if (!quickForm.name || !quickForm.budget) {
      setError('이름과 예산은 필수 입력사항입니다.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // 사용자 등록
      const registrationData: UserRegistration = {
        full_name: quickForm.name,
        email: `${quickForm.name}@temp.com`, // 임시 이메일
        age: parseInt(quickForm.age) || 25,
        phone: ''
      };

      const userResponse = await apiClient.registerUser(registrationData);
      setCurrentUserId(userResponse.user_id);

      // 선호도 저장
      const preferencesData: Omit<UserPreferences, 'user_id'> = {
        budget_min: parseInt(quickForm.budget.split('-')[0]) || 1000,
        budget_max: parseInt(quickForm.budget.split('-')[1]) || 5000,
        fuel_type: quickForm.fuelType || '가솔린',
        category: quickForm.category || '소형',
        family_size: parseInt(quickForm.familySize) || 2,
        usage_purpose: quickForm.purpose || '출퇴근'
      };

      await apiClient.saveUserPreferences(userResponse.user_id, preferencesData);

      // AI 추천 요청
      const chatData = {
        user_id: userResponse.user_id,
        message: `${quickForm.name}님을 위한 차량 추천을 부탁드립니다. 예산: ${quickForm.budget}만원, 연료: ${quickForm.fuelType}, 차종: ${quickForm.category}`,
        context: {
          step: 'quick_recommendation',
          preferences: preferencesData,
          user_info: registrationData
        }
      };

      const response = await apiClient.sendChatMessage(chatData);
      
      if (response.status === 'success') {
        setAiResponse(response.response);
        setRecommendations(response.ml_recommendations || []);
        
        // 채팅에도 결과 추가
        addBotMessage(
          `🎯 ${quickForm.name}님을 위한 맞춤 추천이 완료되었습니다!\n\n` +
          response.response,
          ['더 자세한 상담', '다른 조건으로 재검색', '금융 상담']
        );
      }
    } catch (error) {
      console.error('Quick recommendation failed:', error);
      setError(error instanceof Error ? error.message : '추천 중 오류가 발생했습니다');
    } finally {
      setIsLoading(false);
    }
  };

  // 챗봇 메시지 처리
  const handleChatMessage = async (message: string) => {
    addUserMessage(message);
    setIsTyping(true);

    try {
      if (!currentUserId) {
        // 임시 사용자 생성
        const tempUser: UserRegistration = {
          full_name: '사용자',
          email: 'temp@example.com',
          age: 25
        };
        const userResponse = await apiClient.registerUser(tempUser);
        setCurrentUserId(userResponse.user_id);
      }

      const chatData = {
        user_id: currentUserId!,
        message: message,
        context: {
          step: 'chat_consultation',
          mode: 'hybrid'
        }
      };

      const response = await apiClient.sendChatMessage(chatData);
      
      if (response.status === 'success') {
        setIsTyping(false);
        addBotMessage(
          response.response,
          ['더 자세히', '다른 조건', '금융 상담']
        );

        // ML 추천 결과가 있으면 표시
        if (response.ml_recommendations && response.ml_recommendations.length > 0) {
          setRecommendations(response.ml_recommendations);
          setAiResponse(response.response);
        }
      }
    } catch (error) {
      console.error('Chat failed:', error);
      setIsTyping(false);
      addBotMessage(
        "죄송합니다. 일시적인 문제가 발생했습니다. 다시 시도해주세요.",
        ['다시 시도']
      );
    }
  };

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* 헤더 */}
      <AppBar position="static" elevation={0} sx={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }}>
        <Toolbar>
          <Typography variant="h5" sx={{ flexGrow: 1, fontWeight: 700 }}>
            🚗 CarFin AI - 하이브리드 추천 시스템
          </Typography>
          <Chip label="CrewAI 멀티에이전트" color="secondary" />
          <Chip label="PyCaret ML" color="secondary" sx={{ ml: 1 }} />
        </Toolbar>
      </AppBar>

      {/* 메인 컨텐츠 */}
      <Container maxWidth="xl" sx={{ flex: 1, py: 2 }}>
        <Grid container spacing={2} sx={{ height: '100%' }}>
          {/* 왼쪽: 입력 인터페이스 */}
          <Grid item xs={12} md={6} sx={{ height: '100%' }}>
            <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <Tabs value={activeTab} onChange={handleTabChange}>
                <Tab label="🚀 빠른 추천" />
                <Tab label="💬 AI 상담" />
              </Tabs>
              
              <TabPanel value={activeTab} index={0}>
                <Box sx={{ height: '100%', overflow: 'auto' }}>
                  <Typography variant="h6" gutterBottom>
                    ⚡ 빠른 기본정보 입력
                  </Typography>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="이름"
                        value={quickForm.name}
                        onChange={(e) => setQuickForm(prev => ({ ...prev, name: e.target.value }))}
                        required
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="나이"
                        type="number"
                        value={quickForm.age}
                        onChange={(e) => setQuickForm(prev => ({ ...prev, age: e.target.value }))}
                      />
                    </Grid>
                    
                    <Grid item xs={12}>
                      <FormControl fullWidth required>
                        <InputLabel>예산 범위</InputLabel>
                        <Select
                          value={quickForm.budget}
                          onChange={(e) => setQuickForm(prev => ({ ...prev, budget: e.target.value }))}
                        >
                          <MenuItem value="500-1000">500-1000만원</MenuItem>
                          <MenuItem value="1000-2000">1000-2000만원</MenuItem>
                          <MenuItem value="2000-3000">2000-3000만원</MenuItem>
                          <MenuItem value="3000-5000">3000-5000만원</MenuItem>
                          <MenuItem value="5000-10000">5000만원 이상</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>

                    <Grid item xs={12} sm={6}>
                      <FormControl fullWidth>
                        <InputLabel>연료 타입</InputLabel>
                        <Select
                          value={quickForm.fuelType}
                          onChange={(e) => setQuickForm(prev => ({ ...prev, fuelType: e.target.value }))}
                        >
                          <MenuItem value="가솔린">가솔린</MenuItem>
                          <MenuItem value="디젤">디젤</MenuItem>
                          <MenuItem value="하이브리드">하이브리드</MenuItem>
                          <MenuItem value="전기">전기</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>

                    <Grid item xs={12} sm={6}>
                      <FormControl fullWidth>
                        <InputLabel>차종</InputLabel>
                        <Select
                          value={quickForm.category}
                          onChange={(e) => setQuickForm(prev => ({ ...prev, category: e.target.value }))}
                        >
                          <MenuItem value="소형">소형</MenuItem>
                          <MenuItem value="준중형">준중형</MenuItem>
                          <MenuItem value="중형">중형</MenuItem>
                          <MenuItem value="대형">대형</MenuItem>
                          <MenuItem value="SUV">SUV</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>

                    <Grid item xs={12} sm={6}>
                      <FormControl fullWidth>
                        <InputLabel>가족 구성원</InputLabel>
                        <Select
                          value={quickForm.familySize}
                          onChange={(e) => setQuickForm(prev => ({ ...prev, familySize: e.target.value }))}
                        >
                          <MenuItem value="1">1명</MenuItem>
                          <MenuItem value="2">2명</MenuItem>
                          <MenuItem value="3">3명</MenuItem>
                          <MenuItem value="4">4명</MenuItem>
                          <MenuItem value="5">5명 이상</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>

                    <Grid item xs={12} sm={6}>
                      <FormControl fullWidth>
                        <InputLabel>주 사용 목적</InputLabel>
                        <Select
                          value={quickForm.purpose}
                          onChange={(e) => setQuickForm(prev => ({ ...prev, purpose: e.target.value }))}
                        >
                          <MenuItem value="출퇴근">출퇴근</MenuItem>
                          <MenuItem value="가족여행">가족여행</MenuItem>
                          <MenuItem value="레저">레저</MenuItem>
                          <MenuItem value="업무">업무</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>

                    <Grid item xs={12}>
                      <Button
                        fullWidth
                        variant="contained"
                        size="large"
                        onClick={handleQuickRecommendation}
                        disabled={isLoading}
                        sx={{ mt: 2 }}
                      >
                        {isLoading ? '추천 중...' : '🎯 맞춤 추천 받기'}
                      </Button>
                    </Grid>
                  </Grid>
                  
                  {error && (
                    <Alert severity="error" sx={{ mt: 2 }}>
                      {error}
                    </Alert>
                  )}
                </Box>
              </TabPanel>

              <TabPanel value={activeTab} index={1}>
                <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <Typography variant="h6" gutterBottom>
                    💬 AI 전문가와 상담
                  </Typography>
                  
                  <Box sx={{ flex: 1, overflow: 'auto', mb: 2 }}>
                    {messages.map((message) => (
                      <ChatBubble
                        key={message.id}
                        message={message.message}
                        type={message.type}
                        timestamp={message.timestamp ? new Date(message.timestamp) : undefined}
                        options={message.options}
                        onOptionClick={(option: string) => handleChatMessage(option)}
                      />
                    ))}
                    {isTyping && (
                      <Box sx={{ p: 2 }}>
                        <Typography variant="body2" color="textSecondary">
                          AI가 분석 중입니다...
                        </Typography>
                      </Box>
                    )}
                  </Box>
                  
                  <ChatInput onSendMessage={handleChatMessage} disabled={isLoading} />
                </Box>
              </TabPanel>
            </Paper>
          </Grid>

          {/* 오른쪽: 실시간 추천 결과 */}
          <Grid item xs={12} md={6} sx={{ height: '100%' }}>
            <Paper sx={{ height: '100%', p: 3, overflow: 'auto' }}>
              <Typography variant="h6" gutterBottom>
                🎯 실시간 추천 결과
              </Typography>
              
              {aiResponse && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
                    🤖 AI 전문가 분석
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: '#f5f5f5' }}>
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-line' }}>
                      {aiResponse}
                    </Typography>
                  </Paper>
                </Box>
              )}

              {recommendations.length > 0 && (
                <Box>
                  <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
                    🚗 추천 차량 목록
                  </Typography>
                  <Grid container spacing={2}>
                    {recommendations.map((car) => (
                      <Grid item xs={12} key={car.car_id}>
                        <Card>
                          <CardContent>
                            <Typography variant="h6" gutterBottom>
                              {car.make} {car.model} ({car.year})
                            </Typography>
                            <Box sx={{ mb: 2 }}>
                              <Chip label={`${car.price.toLocaleString()}만원`} color="primary" />
                              <Chip label={car.fuel_type} sx={{ ml: 1 }} />
                              <Chip label={car.category} sx={{ ml: 1 }} />
                            </Box>
                            <Typography variant="body2" color="textSecondary" paragraph>
                              {car.description}
                            </Typography>
                            <Typography variant="body2" sx={{ fontWeight: 600 }}>
                              추천 이유: {car.recommendation_reason}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              )}

              {!aiResponse && recommendations.length === 0 && (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="body1" color="textSecondary">
                    왼쪽에서 빠른 추천을 요청하거나<br />
                    AI와 상담을 시작해보세요! 🚗
                  </Typography>
                </Box>
              )}
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}