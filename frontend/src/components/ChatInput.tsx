import { useState, useRef, useEffect } from 'react';
import {
  Box,
  TextField,
  IconButton,
  Paper,
  InputAdornment,
  Fab
} from '@mui/material';
// @ts-ignore
import { Send, Mic, MicOff } from '@mui/icons-material';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  multiline?: boolean;
}

// ChatInput 컴포넌트 구현
// 사용자가 메시지를 입력하고 전송할 수 있는 입력창
export default function ChatInput({ 
  onSendMessage, 
  disabled = false, 
  placeholder = "메시지를 입력하세요...",
  multiline = false
}: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [isListening, setIsListening] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // 메시지 전송 함수
  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  // Enter 키 처리
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // 음성 인식 (향후 구현 가능)
  const handleVoiceToggle = () => {
    setIsListening(!isListening);
    // 음성 인식 기능은 향후 구현
  };

  // 자동 포커스
  useEffect(() => {
    if (!disabled && inputRef.current) {
      inputRef.current.focus();
    }
  }, [disabled]);

  return (
    <Paper
      elevation={3}
      sx={{
        p: 2,
        backgroundColor: 'white',
        borderTop: '1px solid #e0e0e0'
      }}
    >
      <Box display="flex" alignItems="flex-end" gap={1}>
        <TextField
          ref={inputRef}
          fullWidth
          multiline={multiline}
          maxRows={4}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={placeholder}
          disabled={disabled}
          variant="outlined"
          size="small"
          sx={{
            '& .MuiOutlinedInput-root': {
              borderRadius: '25px',
              backgroundColor: '#f8f9fa',
              '&:hover fieldset': {
                borderColor: '#1976d2',
              },
              '&.Mui-focused fieldset': {
                borderColor: '#1976d2',
              }
            }
          }}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  onClick={handleVoiceToggle}
                  size="small"
                  sx={{ 
                    color: isListening ? '#f44336' : '#666',
                    mr: 0.5
                  }}
                >
                  {isListening ? <MicOff /> : <Mic />}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />
        
        <Fab
          size="small"
          color="primary"
          onClick={handleSend}
          disabled={!message.trim() || disabled}
          sx={{
            minHeight: 40,
            width: 40,
            height: 40
          }}
        >
          <Send />
        </Fab>
      </Box>
      
      {/* 타이핑 힌트 */}
      {!disabled && (
        <Box mt={1} textAlign="center">
          <span style={{ 
            fontSize: '0.75rem', 
            color: '#666',
            fontStyle: 'italic'
          }}>
            Enter를 눌러 전송, Shift+Enter로 줄바꿈
          </span>
        </Box>
      )}
    </Paper>
  );
}