import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Button,
  Collapse,
  IconButton,
  Divider,
  Stack,
  Avatar,
  Rating,
  Fade,
  Tooltip,
} from '@mui/material';

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

interface EnhancedCarCardProps {
  car: CarRecommendation;
  index: number;
  onFinanceConsult: (car: CarRecommendation) => void;
  onCompare: (car: CarRecommendation) => void;
  financeLoading: boolean;
  isSelected?: boolean;
}

const EnhancedCarCard: React.FC<EnhancedCarCardProps> = ({
  car,
  index,
  onFinanceConsult,
  onCompare,
  financeLoading,
  isSelected = false,
}) => {
  const [expanded, setExpanded] = useState(false);
  const [isFavorite, setIsFavorite] = useState(false);

  // Generate brand icon/avatar
  const getBrandIcon = (make: string) => {
    const brandColors: { [key: string]: string } = {
      '현대': '#002c5f',
      '기아': '#05141f',
      'BMW': '#1c69d4',
      '벤츠': '#00adef',
      '아우디': '#bb0a30',
      '토요타': '#eb0a1e',
      '쉐보레': '#ffc72c',
      '닛산': '#c3002f',
    };
    
    return (
      <Avatar 
        sx={{ 
          bgcolor: brandColors[make] || '#1976d2',
          width: 56,
          height: 56,
          fontSize: '1.5rem',
          fontWeight: 'bold',
        }}
      >
        {make.charAt(0)}
      </Avatar>
    );
  };

  const getScoreColor = (score?: number) => {
    if (!score) return 'default';
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    return 'error';
  };

  const formatPrice = (price: number) => {
    if (price >= 10000) {
      const billions = Math.floor(price / 10000);
      const remainder = price % 10000;
      return remainder > 0 ? `${billions}억 ${remainder}만원` : `${billions}억원`;
    }
    return `${price.toLocaleString()}만원`;
  };

  return (
    <Fade in={true} timeout={300 + index * 100}>
      <Card 
        elevation={isSelected ? 8 : 3}
        sx={{ 
          height: '100%', 
          display: 'flex', 
          flexDirection: 'column',
          position: 'relative',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          border: isSelected ? '2px solid #1976d2' : '1px solid transparent',
          '&:hover': {
            transform: 'translateY(-8px) scale(1.02)',
            boxShadow: '0 12px 20px rgba(0,0,0,0.15)',
          }
        }}
      >
        {/* Ranking Badge */}
        <Box
          sx={{
            position: 'absolute',
            top: -10,
            left: 16,
            zIndex: 2,
          }}
        >
          <Chip 
            label={`추천 ${index + 1}`} 
            color="primary" 
            size="small"
            sx={{
              fontWeight: 'bold',
              fontSize: '0.75rem',
              boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
            }}
          />
        </Box>

        {/* Score Badge */}
        {car.score && (
          <Box
            sx={{
              position: 'absolute',
              top: -10,
              right: 16,
              zIndex: 2,
            }}
          >
            <Chip 
              label={`${Math.round((car.score || 0) * 100)}점`} 
              color={getScoreColor(car.score)}
              size="small"
              sx={{
                fontWeight: 'bold',
                fontSize: '0.75rem',
                boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
              }}
            />
          </Box>
        )}

        <CardContent sx={{ flexGrow: 1, pt: 3 }}>
          {/* Header with Brand Icon */}
          <Box display="flex" alignItems="center" gap={2} mb={2}>
            {getBrandIcon(car.make)}
            <Box flex={1}>
              <Typography variant="h6" sx={{ fontWeight: 600, lineHeight: 1.2 }}>
                {car.make} {car.model}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                {car.year}년 • {car.category}
              </Typography>
            </Box>
            <IconButton
              onClick={() => setIsFavorite(!isFavorite)}
              sx={{ color: isFavorite ? '#f44336' : '#ccc' }}
            >
              {isFavorite ? '❤️' : '🤍'}
            </IconButton>
          </Box>
          
          {/* Price - Most Prominent */}
          <Box textAlign="center" mb={2}>
            <Typography 
              variant="h4" 
              sx={{ 
                fontWeight: 700,
                background: 'linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}
            >
              {formatPrice(car.price)}
            </Typography>
          </Box>
          
          {/* Key Specs */}
          <Stack direction="row" spacing={1} justifyContent="center" mb={2} flexWrap="wrap">
            <Chip 
              label={car.fuel_type} 
              size="small" 
              variant="outlined"
              color="info"
            />
            {car.fuel_efficiency && (
              <Chip 
                label={`${car.fuel_efficiency}km/L`} 
                size="small" 
                variant="outlined"
                color="success"
              />
            )}
            <Chip 
              label={
                <Box display="flex" alignItems="center" gap={0.5}>
                  <span>안전</span>
                  <Rating 
                    value={car.safety_rating} 
                    max={5} 
                    size="small" 
                    readOnly 
                    sx={{ fontSize: '0.8rem' }}
                  />
                </Box>
              }
              size="small" 
              variant="outlined"
              color="warning"
            />
          </Stack>
          
          {/* Recommendation Reason */}
          <Box mb={2}>
            <Typography 
              variant="body2" 
              sx={{ 
                fontWeight: 500,
                color: '#1976d2',
                textAlign: 'center',
                fontStyle: 'italic',
              }}
            >
              "⭐ {car.recommendation_reason}"
            </Typography>
          </Box>

          {/* Expandable Details */}
          <Box>
            <Button
              variant="text"
              onClick={() => setExpanded(!expanded)}
              sx={{ width: '100%', mb: 1 }}
            >
              {expanded ? '▲ 간단히' : '▼ 자세히'}
            </Button>
            
            <Collapse in={expanded}>
              <Divider sx={{ my: 1 }} />
              <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                {car.description}
              </Typography>
              
              {/* Detailed Specs */}
              <Box display="grid" gridTemplateColumns="1fr 1fr" gap={1} mb={2}>
                <Box>
                  <Typography variant="caption" color="textSecondary">
                    연식
                  </Typography>
                  <Typography variant="body2" fontWeight="500">
                    {car.year}년
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="textSecondary">
                    차종
                  </Typography>
                  <Typography variant="body2" fontWeight="500">
                    {car.category}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="textSecondary">
                    연료
                  </Typography>
                  <Typography variant="body2" fontWeight="500">
                    {car.fuel_type}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="textSecondary">
                    연비
                  </Typography>
                  <Typography variant="body2" fontWeight="500">
                    {car.fuel_efficiency}km/L
                  </Typography>
                </Box>
              </Box>
            </Collapse>
          </Box>
          
          {/* Action Buttons */}
          <Stack spacing={1} mt={2}>
            <Button
              variant="contained"
              onClick={() => onFinanceConsult(car)}
              disabled={financeLoading}
              sx={{
                py: 1.2,
                fontWeight: 600,
                background: 'linear-gradient(45deg, #4caf50 30%, #66bb6a 90%)',
                '&:hover': {
                  background: 'linear-gradient(45deg, #388e3c 30%, #4caf50 90%)',
                }
              }}
            >
              {financeLoading ? '💰 상담 중...' : '💰 금융 상담'}
            </Button>
            
            <Stack direction="row" spacing={1}>
              <Button
                variant="outlined"
                onClick={() => onCompare(car)}
                sx={{ flex: 1 }}
              >
                📊 비교
              </Button>
              <Tooltip title="차량 정보 공유">
                <Button
                  variant="outlined"
                  sx={{ minWidth: 'auto', px: 1.5 }}
                >
                  📤
                </Button>
              </Tooltip>
            </Stack>
          </Stack>
        </CardContent>
      </Card>
    </Fade>
  );
};

export default EnhancedCarCard;