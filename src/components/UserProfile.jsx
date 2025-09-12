import React, { useState } from 'react';
import {
  Paper,
  TextField,
  Button,
  Grid,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Box,
  Chip,
  FormGroup,
  FormControlLabel,
  Checkbox
} from '@mui/material';
import SaveIcon from '@mui/icons-material/Save';

const UserProfile = () => {
  const [profile, setProfile] = useState({
    budget: 3000,
    purpose: '',
    experience: '',
    preferredBrands: [],
    fuelType: '',
    familySize: 1,
    lifestyle: ''
  });

  const handleProfileChange = (field, value) => {
    setProfile(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleBrandToggle = (brand) => {
    setProfile(prev => ({
      ...prev,
      preferredBrands: prev.preferredBrands.includes(brand)
        ? prev.preferredBrands.filter(b => b !== brand)
        : [...prev.preferredBrands, brand]
    }));
  };

  const handleSaveProfile = () => {
    console.log('저장할 프로필:', profile);
    // TODO: API 호출로 프로필 저장
    alert('프로필이 저장되었습니다!');
  };

  const brands = ['현대', '기아', '삼성', '쌍용', 'BMW', '벤츠', '아우디', '도요타', '혼다'];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        사용자 프로필
      </Typography>
      
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          맞춤 추천을 위한 정보를 입력해주세요
        </Typography>
        
        <Grid container spacing={3}>
          {/* 예산 */}
          <Grid item xs={12}>
            <Typography gutterBottom>
              예산: {profile.budget.toLocaleString()}만원
            </Typography>
            <Slider
              value={profile.budget}
              onChange={(e, value) => handleProfileChange('budget', value)}
              min={1000}
              max={10000}
              step={100}
              valueLabelDisplay="auto"
              valueLabelFormat={value => `${value.toLocaleString()}만원`}
            />
          </Grid>

          {/* 구매 목적 */}
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>구매 목적</InputLabel>
              <Select
                value={profile.purpose}
                onChange={(e) => handleProfileChange('purpose', e.target.value)}
                label="구매 목적"
              >
                <MenuItem value="출퇴근">출퇴근</MenuItem>
                <MenuItem value="가족용">가족용</MenuItem>
                <MenuItem value="레저">레저/여행</MenuItem>
                <MenuItem value="비즈니스">비즈니스</MenuItem>
                <MenuItem value="첫차">첫차</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {/* 운전 경력 */}
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>운전 경력</InputLabel>
              <Select
                value={profile.experience}
                onChange={(e) => handleProfileChange('experience', e.target.value)}
                label="운전 경력"
              >
                <MenuItem value="초보">초보 (1년 미만)</MenuItem>
                <MenuItem value="일반">일반 (1-5년)</MenuItem>
                <MenuItem value="숙련">숙련 (5년 이상)</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {/* 연료 타입 */}
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>선호 연료</InputLabel>
              <Select
                value={profile.fuelType}
                onChange={(e) => handleProfileChange('fuelType', e.target.value)}
                label="선호 연료"
              >
                <MenuItem value="가솔린">가솔린</MenuItem>
                <MenuItem value="디젤">디젤</MenuItem>
                <MenuItem value="하이브리드">하이브리드</MenuItem>
                <MenuItem value="전기">전기</MenuItem>
                <MenuItem value="상관없음">상관없음</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {/* 가족 구성원 */}
          <Grid item xs={12} sm={6}>
            <Typography gutterBottom>
              가족 구성원: {profile.familySize}명
            </Typography>
            <Slider
              value={profile.familySize}
              onChange={(e, value) => handleProfileChange('familySize', value)}
              min={1}
              max={8}
              step={1}
              marks
              valueLabelDisplay="auto"
            />
          </Grid>

          {/* 선호 브랜드 */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              선호 브랜드 (복수 선택 가능)
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {brands.map((brand) => (
                <Chip
                  key={brand}
                  label={brand}
                  clickable
                  color={profile.preferredBrands.includes(brand) ? 'primary' : 'default'}
                  onClick={() => handleBrandToggle(brand)}
                />
              ))}
            </Box>
          </Grid>

          {/* 라이프스타일 */}
          <Grid item xs={12}>
            <FormControl fullWidth>
              <InputLabel>라이프스타일</InputLabel>
              <Select
                value={profile.lifestyle}
                onChange={(e) => handleProfileChange('lifestyle', e.target.value)}
                label="라이프스타일"
              >
                <MenuItem value="도심형">도심형 (주차 편의성 중시)</MenuItem>
                <MenuItem value="활동적">활동적 (여행, 아웃도어)</MenuItem>
                <MenuItem value="실용적">실용적 (연비, 유지비 중시)</MenuItem>
                <MenuItem value="럭셔리">럭셔리 (브랜드, 옵션 중시)</MenuItem>
                <MenuItem value="스포티">스포티 (성능, 디자인 중시)</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          {/* 저장 버튼 */}
          <Grid item xs={12}>
            <Button
              variant="contained"
              size="large"
              startIcon={<SaveIcon />}
              onClick={handleSaveProfile}
              fullWidth
            >
              프로필 저장
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* 현재 프로필 요약 */}
      <Paper elevation={2} sx={{ p: 2, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          현재 프로필 요약
        </Typography>
        <Typography variant="body2">
          예산: {profile.budget.toLocaleString()}만원 | 
          목적: {profile.purpose || '미설정'} | 
          경력: {profile.experience || '미설정'} | 
          연료: {profile.fuelType || '미설정'}
        </Typography>
        {profile.preferredBrands.length > 0 && (
          <Box sx={{ mt: 1 }}>
            <Typography variant="body2" component="span">선호 브랜드: </Typography>
            {profile.preferredBrands.map((brand, index) => (
              <Chip key={brand} label={brand} size="small" sx={{ mr: 0.5 }} />
            ))}
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default UserProfile;