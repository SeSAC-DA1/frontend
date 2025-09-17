import { 
  Box, 
  Typography, 
  Avatar, 
  Paper,
  Fade,
  Chip
} from '@mui/material';
// @ts-ignore
import { SmartToy, Person } from '@mui/icons-material';

interface ChatBubbleProps {
  message: string;
  type: 'user' | 'bot';
  timestamp?: Date;
  showTyping?: boolean;
  options?: string[];
  onOptionClick?: (option: string) => void;
}

// ChatBubble 컴포넌트 구현
// 사용자와 봇의 메시지를 구분하여 표시
export default function ChatBubble({ 
  message, 
  type, 
  timestamp, 
  showTyping = false,
  options = [],
  onOptionClick 
}: ChatBubbleProps) {
  const isBot = type === 'bot';
  
  return (
    <Fade in={true} timeout={500}>
      <Box
        display="flex"
        justifyContent={isBot ? 'flex-start' : 'flex-end'}
        alignItems="flex-start"
        mb={2}
        gap={1}
      >
        {/* 봇 아바타 (왼쪽) */}
        {isBot && (
          <Avatar 
            sx={{ 
              bgcolor: '#1976d2', 
              width: 35, 
              height: 35,
              mt: 0.5
            }}
          >
            <SmartToy fontSize="small" />
          </Avatar>
        )}
        
        {/* 메시지 컨텐츠 */}
        <Box maxWidth="75%">
          <Paper
            elevation={1}
            sx={{
              p: 2,
              backgroundColor: isBot ? '#f5f5f5' : '#1976d2',
              color: isBot ? '#333' : 'white',
              borderRadius: isBot ? '18px 18px 18px 5px' : '18px 18px 5px 18px',
              position: 'relative'
            }}
          >
            {showTyping ? (
              <Box display="flex" alignItems="center" gap={0.5}>
                <Typography variant="body2">입력 중</Typography>
                <Box display="flex" gap={0.2}>
                  {[0, 1, 2].map((dot) => (
                    <Box
                      key={dot}
                      sx={{
                        width: 4,
                        height: 4,
                        borderRadius: '50%',
                        backgroundColor: '#666',
                        animation: 'typing 1.4s infinite',
                        animationDelay: `${dot * 0.2}s`,
                        '@keyframes typing': {
                          '0%, 60%, 100%': { opacity: 0.3 },
                          '30%': { opacity: 1 }
                        }
                      }}
                    />
                  ))}
                </Box>
              </Box>
            ) : (
              <Typography 
                variant="body1" 
                sx={{ 
                  whiteSpace: 'pre-line',
                  fontSize: '1rem',
                  lineHeight: 1.5
                }}
              >
                {message}
              </Typography>
            )}
          </Paper>
          
          {/* 옵션 버튼들 (봇 메시지에만) */}
          {isBot && options.length > 0 && (
            <Box mt={1} display="flex" flexWrap="wrap" gap={1}>
              {options.map((option, index) => (
                <Chip
                  key={index}
                  label={option}
                  onClick={() => onOptionClick?.(option)}
                  sx={{
                    backgroundColor: '#e3f2fd',
                    color: '#1976d2',
                    '&:hover': {
                      backgroundColor: '#bbdefb'
                    },
                    cursor: 'pointer'
                  }}
                />
              ))}
            </Box>
          )}
          
          {/* 타임스탬프 */}
          {timestamp && (
            <Typography 
              variant="caption" 
              color="textSecondary" 
              display="block" 
              textAlign={isBot ? 'left' : 'right'}
              mt={0.5}
            >
              {timestamp.toLocaleTimeString('ko-KR', { 
                hour: '2-digit', 
                minute: '2-digit' 
              })}
            </Typography>
          )}
        </Box>
        
        {/* 사용자 아바타 (오른쪽) */}
        {!isBot && (
          <Avatar 
            sx={{ 
              bgcolor: '#4caf50', 
              width: 35, 
              height: 35,
              mt: 0.5
            }}
          >
            <Person fontSize="small" />
          </Avatar>
        )}
      </Box>
    </Fade>
  );
}