import React, { useState } from 'react';
import {
  Container,
  Box,
  Typography,
  Grid,
  Alert,
  Paper,
  Divider,
  Skeleton,
  Fade,
  Card,
  CardContent,
} from '@mui/material';
import GuidedInputPanel from './GuidedInputPanel';
import EnhancedHeader from './EnhancedHeader';
import EnhancedCarCard from './EnhancedCarCard';

// Types for API responses
interface CarRecommendation {
  car_id: number;
  make: string;
  model: string;
  year: number;
  price: number;
  fuel_type: string;
  category: string;
  fuel_efficiency?: number;
  safety_rating: number;
  description: string;
  recommendation_reason: string;
  score?: number;
}

interface RecommendationResponse {
  status: string;
  agent_response: string;
  ml_recommendations: CarRecommendation[];
  user_profile: any;
  message?: string;
}

interface FinanceOption {
  type: string;
  monthly_payment: number;
  total_cost: number;
  down_payment: number;
  description: string;
}

interface FinanceResponse {
  status: string;
  agent_response: string;
  car_details: any;
  finance_options: FinanceOption[];
  message?: string;
}

interface CarRecommendationAppProps {
  onStartChat: () => void;
}

const CarRecommendationApp: React.FC<CarRecommendationAppProps> = ({ onStartChat }) => {
  const [recommendations, setRecommendations] = useState<CarRecommendation[]>([]);
  const [agentResponse, setAgentResponse] = useState('');
  const [financeInfo, setFinanceInfo] = useState<FinanceResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [financeLoading, setFinanceLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedCar, setSelectedCar] = useState<CarRecommendation | null>(null);
  const [compareList, setCompareList] = useState<CarRecommendation[]>([]);
  const [agentLoading, setAgentLoading] = useState(false);

  // Get backend URL - backend runs on port 8000, frontend on 5000
  const API_BASE = window.location.protocol + '//' + window.location.hostname + ':8000';

  const handleRecommendation = async (inputData: {
    message: string;
    budget: number;
    filters: any;
  }) => {
    if (!inputData.message.trim() && !Object.values(inputData.filters).some(v => v)) {
      setError('메시지를 입력하거나 조건을 선택해주세요.');
      return;
    }

    setLoading(true);
    setAgentLoading(true);
    setError('');
    setRecommendations([]);
    setAgentResponse('');
    setFinanceInfo(null);
    setSelectedCar(null);

    try {
      const response = await fetch(`${API_BASE}/api/recommend`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputData.message,
          user_id: 'user_' + Date.now(),
          budget: inputData.budget,
          filters: inputData.filters,
        }),
      });

      if (!response.ok) {
        throw new Error(`서버 오류: ${response.status}`);
      }

      const data: RecommendationResponse = await response.json();

      if (data.status === 'error') {
        throw new Error(data.message || '추천을 가져오는 중 오류가 발생했습니다.');
      }

      // 에이전트 응답 먼저 표시
      setAgentResponse(data.agent_response || '');
      setAgentLoading(false);
      
      // 추천 결과는 조금 뒤에 표시 (더 나은 UX)
      setTimeout(() => {
        setRecommendations(data.ml_recommendations || []);
        setLoading(false);
      }, 500);
      
    } catch (err) {
      console.error('Recommendation error:', err);
      setError(err instanceof Error ? err.message : '추천 요청 중 오류가 발생했습니다.');
      setLoading(false);
      setAgentLoading(false);
    }
  };

  const handleFinanceConsult = async (car: CarRecommendation) => {
    setFinanceLoading(true);
    setSelectedCar(car);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/api/finance`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          car_id: car.car_id.toString(),
          user_budget: car.price, // 차량 가격을 기본 예산으로 사용
        }),
      });

      if (!response.ok) {
        throw new Error(`서버 오류: ${response.status}`);
      }

      const data: FinanceResponse = await response.json();

      if (data.status === 'error') {
        throw new Error(data.message || '금융 상담 중 오류가 발생했습니다.');
      }

      setFinanceInfo(data);
    } catch (err) {
      console.error('Finance consultation error:', err);
      setError(err instanceof Error ? err.message : '금융 상담 요청 중 오류가 발생했습니다.');
    } finally {
      setFinanceLoading(false);
    }
  };

  const handleCompare = (car: CarRecommendation) => {
    if (compareList.find(c => c.car_id === car.car_id)) {
      setCompareList(compareList.filter(c => c.car_id !== car.car_id));
    } else if (compareList.length < 3) {
      setCompareList([...compareList, car]);
    }
  };

  return (
    <Box>
      {/* Enhanced Header */}
      <EnhancedHeader onStartChat={onStartChat} />
      
      <Container maxWidth="lg" sx={{ py: 2 }}>
        {/* Guided Input Panel */}
        <GuidedInputPanel 
          onSubmit={handleRecommendation}
          loading={loading}
        />

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

        {/* Agent Response with Loading */}
        {(agentLoading || agentResponse) && (
          <Paper 
            elevation={2} 
            sx={{ 
              p: 3, 
              mb: 4, 
              background: 'linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%)',
              borderRadius: 3,
            }}
          >
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, color: '#1976d2' }}>
              🤖 AI 전문가 분석
            </Typography>
            {agentLoading ? (
              <Box>
                <Skeleton variant="text" width="80%" height={32} />
                <Skeleton variant="text" width="60%" height={32} />
                <Skeleton variant="text" width="90%" height={32} />
              </Box>
            ) : (
              <Fade in={!!agentResponse}>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-line', fontSize: '1.05rem', lineHeight: 1.6 }}>
                  {agentResponse}
                </Typography>
              </Fade>
            )}
          </Paper>
        )}

        {/* Car Recommendations with Loading Skeletons */}
        {(loading || recommendations.length > 0) && (
          <Box mb={4}>
            <Typography variant="h5" gutterBottom sx={{ mb: 3, fontWeight: 600, color: '#1976d2' }}>
              🎯 맞춤 추천 차량
              {compareList.length > 0 && (
                <Typography component="span" variant="body2" color="textSecondary" sx={{ ml: 2 }}>
                  (비교 목록: {compareList.length}/3)
                </Typography>
              )}
            </Typography>
            
            <Grid container spacing={3}>
              {loading ? (
                // Loading Skeletons
                Array.from({ length: 3 }).map((_, index) => (
                  <Grid item xs={12} md={4} key={`skeleton-${index}`}>
                    <Paper sx={{ p: 2, height: 400 }}>
                      <Skeleton variant="circular" width={56} height={56} sx={{ mb: 2 }} />
                      <Skeleton variant="text" width="80%" height={32} />
                      <Skeleton variant="text" width="60%" height={24} />
                      <Skeleton variant="text" width="100%" height={48} sx={{ my: 2 }} />
                      <Skeleton variant="rectangular" width="100%" height={100} />
                    </Paper>
                  </Grid>
                ))
              ) : (
                // Actual Recommendations
                recommendations.map((car, index) => (
                  <Grid item xs={12} md={4} key={car.car_id}>
                    <EnhancedCarCard
                      car={car}
                      index={index}
                      onFinanceConsult={handleFinanceConsult}
                      onCompare={handleCompare}
                      financeLoading={financeLoading && selectedCar?.car_id === car.car_id}
                      isSelected={compareList.find(c => c.car_id === car.car_id) !== undefined}
                    />
                  </Grid>
                ))
              )}
            </Grid>
          </Box>
        )}

      {/* Finance Information */}
      {financeInfo && selectedCar && (
        <Paper elevation={3} sx={{ p: 4 }}>
          <Typography variant="h5" gutterBottom>
            💳 {selectedCar.make} {selectedCar.model} 금융 상담 결과
          </Typography>
          
          {financeInfo.agent_response && (
            <Box mb={3}>
              <Typography variant="h6" gutterBottom>
                전문가 분석
              </Typography>
              <Typography variant="body1" sx={{ whiteSpace: 'pre-line', mb: 2 }}>
                {financeInfo.agent_response}
              </Typography>
              <Divider />
            </Box>
          )}
          
          <Typography variant="h6" gutterBottom>
            금융 옵션 비교
          </Typography>
          
          <Grid container spacing={3}>
            {financeInfo.finance_options.map((option, index) => (
              <Grid item xs={12} md={6} key={index}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" color="primary" gutterBottom>
                      {option.type}
                    </Typography>
                    
                    <Box mb={2}>
                      <Typography variant="body2" color="textSecondary">
                        월 납부액
                      </Typography>
                      <Typography variant="h6">
                        {option.monthly_payment === 0 
                          ? '없음' 
                          : `${option.monthly_payment.toLocaleString()}만원`}
                      </Typography>
                    </Box>
                    
                    <Box mb={2}>
                      <Typography variant="body2" color="textSecondary">
                        총 지급 비용
                      </Typography>
                      <Typography variant="h6">
                        {option.total_cost.toLocaleString()}만원
                      </Typography>
                    </Box>
                    
                    <Box mb={2}>
                      <Typography variant="body2" color="textSecondary">
                        초기 납입금
                      </Typography>
                      <Typography variant="h6">
                        {option.down_payment.toLocaleString()}만원
                      </Typography>
                    </Box>
                    
                    <Typography variant="body2" color="textSecondary">
                      {option.description}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

        {/* Footer */}
        <Box textAlign="center" mt={6} py={3}>
          <Typography variant="body2" color="textSecondary">
            CarFin AI - 엔카 실제 매물 데이터 × CrewAI 멀티에이전트 × PyCaret ML 추천 시스템
          </Typography>
          <Typography variant="caption" color="textSecondary" display="block" mt={1}>
            Powered by OpenAI GPT-4 & 실시간 차량 데이터
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default CarRecommendationApp;