import React, { useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  Chip,
  Slider,
  Button,
  Paper,
  Grid,
  Stack,
  Fade,
  Collapse,
  IconButton,
} from '@mui/material';

interface GuidedInputPanelProps {
  onSubmit: (data: {
    message: string;
    budget: number;
    filters: {
      purpose?: string;
      category?: string;
      fuel?: string;
      transmission?: string;
    };
  }) => void;
  loading: boolean;
}

const GuidedInputPanel: React.FC<GuidedInputPanelProps> = ({ onSubmit, loading }) => {
  const [message, setMessage] = useState('');
  const [budget, setBudget] = useState(4000);
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  // Quick pick filters
  const [selectedPurpose, setSelectedPurpose] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedFuel, setSelectedFuel] = useState<string | null>(null);
  const [selectedTransmission, setSelectedTransmission] = useState<string | null>(null);

  // Quick pick options
  const purposes = [
    '첫차 구입', '가족용', '출퇴근용', '주말드라이브', '사업용', '연비중심'
  ];
  
  const categories = [
    'Sedan', 'SUV', 'Hatchback', 'Mini'
  ];
  
  const fuels = [
    '가솔린', '디젤', '하이브리드', '전기', 'LPG'
  ];
  
  const transmissions = [
    '자동', '수동', 'CVT'
  ];

  // Suggested prompts
  const suggestions = [
    "30대 직장인용 연비 좋은 첫 차 추천해주세요",
    "4인 가족용 안전한 SUV를 찾고 있어요",
    "출퇴근용으로 경제적인 소형차가 필요해요",
    "주말 드라이브용 스타일리쉬한 차량 추천",
    "연비와 실용성을 모두 갖춘 차량이 필요해요"
  ];

  const handleSubmit = () => {
    let finalMessage = message;
    
    // Add selected filters to message if they exist
    const filterParts = [];
    if (selectedPurpose) filterParts.push(`용도: ${selectedPurpose}`);
    if (selectedCategory) filterParts.push(`차종: ${selectedCategory}`);
    if (selectedFuel) filterParts.push(`연료: ${selectedFuel}`);
    if (selectedTransmission) filterParts.push(`변속기: ${selectedTransmission}`);
    
    if (filterParts.length > 0) {
      finalMessage = `${message} (${filterParts.join(', ')})`;
    }

    onSubmit({
      message: finalMessage,
      budget,
      filters: {
        purpose: selectedPurpose || undefined,
        category: selectedCategory || undefined,
        fuel: selectedFuel || undefined,
        transmission: selectedTransmission || undefined,
      }
    });
  };

  const formatBudget = (value: number) => `${value.toLocaleString()}만원`;

  const isFormValid = message.trim() || selectedPurpose || selectedCategory;

  return (
    <Paper 
      elevation={3} 
      sx={{ 
        p: 4, 
        mb: 4,
        background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
        borderRadius: 3,
      }}
    >
      <Box mb={3}>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, color: '#1976d2' }}>
          🎯 AI 차량 추천 받기
        </Typography>
        <Typography variant="body1" color="textSecondary">
          원하는 조건을 선택하거나 자유롭게 설명해보세요
        </Typography>
      </Box>

      {/* Quick Pick Filters */}
      <Box mb={3}>
        <Typography variant="h6" gutterBottom sx={{ fontWeight: 500 }}>
          빠른 선택
        </Typography>
        
        {/* Purpose */}
        <Box mb={2}>
          <Typography variant="subtitle2" gutterBottom color="textSecondary">
            구매 목적
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            {purposes.map((purpose) => (
              <Chip
                key={purpose}
                label={purpose}
                clickable
                color={selectedPurpose === purpose ? "primary" : "default"}
                variant={selectedPurpose === purpose ? "filled" : "outlined"}
                onClick={() => setSelectedPurpose(selectedPurpose === purpose ? null : purpose)}
                sx={{ mb: 1 }}
              />
            ))}
          </Stack>
        </Box>

        {/* Category */}
        <Box mb={2}>
          <Typography variant="subtitle2" gutterBottom color="textSecondary">
            차종
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            {categories.map((category) => (
              <Chip
                key={category}
                label={category}
                clickable
                color={selectedCategory === category ? "secondary" : "default"}
                variant={selectedCategory === category ? "filled" : "outlined"}
                onClick={() => setSelectedCategory(selectedCategory === category ? null : category)}
                sx={{ mb: 1 }}
              />
            ))}
          </Stack>
        </Box>

        {/* Advanced Filters */}
        <Box>
          <Button
            variant="text"
            onClick={() => setShowAdvanced(!showAdvanced)}
            sx={{ mb: 1 }}
          >
            {showAdvanced ? '▼' : '▶'} 상세 옵션
          </Button>
          
          <Collapse in={showAdvanced}>
            <Box mt={2}>
              {/* Fuel Type */}
              <Box mb={2}>
                <Typography variant="subtitle2" gutterBottom color="textSecondary">
                  연료 타입
                </Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                  {fuels.map((fuel) => (
                    <Chip
                      key={fuel}
                      label={fuel}
                      clickable
                      color={selectedFuel === fuel ? "success" : "default"}
                      variant={selectedFuel === fuel ? "filled" : "outlined"}
                      onClick={() => setSelectedFuel(selectedFuel === fuel ? null : fuel)}
                      sx={{ mb: 1 }}
                    />
                  ))}
                </Stack>
              </Box>

              {/* Transmission */}
              <Box mb={2}>
                <Typography variant="subtitle2" gutterBottom color="textSecondary">
                  변속기
                </Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                  {transmissions.map((transmission) => (
                    <Chip
                      key={transmission}
                      label={transmission}
                      clickable
                      color={selectedTransmission === transmission ? "info" : "default"}
                      variant={selectedTransmission === transmission ? "filled" : "outlined"}
                      onClick={() => setSelectedTransmission(selectedTransmission === transmission ? null : transmission)}
                      sx={{ mb: 1 }}
                    />
                  ))}
                </Stack>
              </Box>
            </Box>
          </Collapse>
        </Box>
      </Box>

      {/* Budget Slider */}
      <Box mb={3}>
        <Typography variant="h6" gutterBottom sx={{ fontWeight: 500 }}>
          예산 범위
        </Typography>
        <Box px={2}>
          <Slider
            value={budget}
            onChange={(_, value) => setBudget(value as number)}
            min={1000}
            max={10000}
            step={100}
            marks={[
              { value: 1000, label: '1천만원' },
              { value: 3000, label: '3천만원' },
              { value: 5000, label: '5천만원' },
              { value: 8000, label: '8천만원' },
              { value: 10000, label: '1억원' },
            ]}
            valueLabelDisplay="auto"
            valueLabelFormat={formatBudget}
            sx={{ mt: 2, mb: 1 }}
          />
          <Typography variant="body2" color="primary" textAlign="center" fontWeight="bold">
            현재 예산: {formatBudget(budget)}
          </Typography>
        </Box>
      </Box>

      {/* Free Text Input */}
      <Box mb={3}>
        <Typography variant="h6" gutterBottom sx={{ fontWeight: 500 }}>
          상세 요청사항 (선택)
        </Typography>
        <TextField
          fullWidth
          multiline
          rows={3}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="더 구체적인 요구사항이 있다면 자유롭게 설명해주세요..."
          variant="outlined"
          disabled={loading}
          sx={{ mb: 2 }}
        />
        
        {/* Suggestion chips */}
        <Box>
          <Typography variant="subtitle2" gutterBottom color="textSecondary">
            💡 추천 문구 (클릭해서 사용)
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            {suggestions.map((suggestion, index) => (
              <Chip
                key={index}
                label={suggestion}
                clickable
                variant="outlined"
                size="small"
                onClick={() => setMessage(suggestion)}
                sx={{ mb: 1, fontSize: '0.75rem' }}
              />
            ))}
          </Stack>
        </Box>
      </Box>

      {/* Submit Button */}
      <Box textAlign="center">
        <Button
          variant="contained"
          size="large"
          onClick={handleSubmit}
          disabled={loading || !isFormValid}
          sx={{
            px: 6,
            py: 1.5,
            fontSize: '1.1rem',
            fontWeight: 600,
            borderRadius: 3,
            background: 'linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)',
            '&:hover': {
              background: 'linear-gradient(45deg, #1565c0 30%, #1976d2 90%)',
            }
          }}
        >
          {loading ? '🤖 AI 분석 중...' : '🚀 맞춤 추천 받기'}
        </Button>
        
        {isFormValid && (
          <Fade in={true}>
            <Typography variant="body2" color="success.main" sx={{ mt: 1 }}>
              ✅ 조건이 설정되었습니다
            </Typography>
          </Fade>
        )}
      </Box>
    </Paper>
  );
};

export default GuidedInputPanel;