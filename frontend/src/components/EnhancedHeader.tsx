import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  Container,
  Chip,
  Button,
} from '@mui/material';

interface EnhancedHeaderProps {
  onStartChat: () => void;
}

const EnhancedHeader: React.FC<EnhancedHeaderProps> = ({ onStartChat }) => {
  return (
    <AppBar 
      position="static" 
      elevation={0}
      sx={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        mb: 4,
      }}
    >
      <Container maxWidth="lg">
        <Toolbar sx={{ justifyContent: 'space-between', py: 2 }}>
          <Box display="flex" alignItems="center" gap={2}>
            <Typography 
              variant="h4" 
              component="h1" 
              sx={{ 
                fontWeight: 700,
                background: 'linear-gradient(45deg, #fff 30%, #e3f2fd 90%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}
            >
              🚗 CarFin AI
            </Typography>
            <Chip 
              label="Beta" 
              size="small" 
              sx={{ 
                backgroundColor: 'rgba(255,255,255,0.2)',
                color: 'white',
                fontWeight: 600,
              }}
            />
          </Box>
          
          <Box display="flex" alignItems="center" gap={2}>
            <Chip 
              label="🤖 CrewAI 멀티에이전트" 
              variant="outlined"
              sx={{ 
                color: 'white',
                borderColor: 'rgba(255,255,255,0.5)',
                '&:hover': {
                  backgroundColor: 'rgba(255,255,255,0.1)',
                }
              }}
            />
            <Chip 
              label="🧠 PyCaret ML" 
              variant="outlined"
              sx={{ 
                color: 'white',
                borderColor: 'rgba(255,255,255,0.5)',
                '&:hover': {
                  backgroundColor: 'rgba(255,255,255,0.1)',
                }
              }}
            />
            <Button
              variant="contained"
              onClick={onStartChat}
              sx={{
                backgroundColor: 'rgba(255,255,255,0.2)',
                color: 'white',
                fontWeight: 600,
                borderRadius: 3,
                px: 3,
                '&:hover': {
                  backgroundColor: 'rgba(255,255,255,0.3)',
                }
              }}
            >
              💬 AI 상담 시작
            </Button>
          </Box>
        </Toolbar>
        
        {/* Hero Section */}
        <Box textAlign="center" pb={4}>
          <Typography 
            variant="h5" 
            sx={{ 
              color: 'rgba(255,255,255,0.9)',
              fontWeight: 400,
              mb: 1,
            }}
          >
            인공지능이 추천하는 완벽한 차량
          </Typography>
          <Typography 
            variant="body1" 
            sx={{ 
              color: 'rgba(255,255,255,0.7)',
              maxWidth: 600,
              mx: 'auto',
            }}
          >
            엔카 실제 매물 데이터와 AI 전문가가 당신에게 최적의 차량과 금융 옵션을 제안합니다
          </Typography>
        </Box>
      </Container>
    </AppBar>
  );
};

export default EnhancedHeader;