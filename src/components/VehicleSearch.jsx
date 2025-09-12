import React, { useState } from 'react';
import {
  Paper,
  TextField,
  Button,
  Grid,
  Typography,
  Card,
  CardContent,
  CardMedia,
  Box,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';

const VehicleSearch = () => {
  const [searchFilters, setSearchFilters] = useState({
    make: '',
    model: '',
    minPrice: '',
    maxPrice: '',
    minYear: '',
    maxYear: ''
  });

  // 임시 더미 데이터
  const [vehicles] = useState([
    {
      id: 1,
      make: '현대',
      model: '아반떼',
      year: 2022,
      price: 2300,
      mileage: 15000,
      image: 'https://via.placeholder.com/300x200?text=아반떼',
      details: { color: '흰색', fuel: '가솔린' }
    },
    {
      id: 2,
      make: '기아',
      model: 'K5',
      year: 2021,
      price: 2800,
      mileage: 25000,
      image: 'https://via.placeholder.com/300x200?text=K5',
      details: { color: '검정', fuel: '가솔린' }
    },
    {
      id: 3,
      make: '삼성',
      model: 'SM6',
      year: 2020,
      price: 2200,
      mileage: 35000,
      image: 'https://via.placeholder.com/300x200?text=SM6',
      details: { color: '회색', fuel: '가솔린' }
    }
  ]);

  const handleFilterChange = (field, value) => {
    setSearchFilters(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSearch = () => {
    console.log('검색 필터:', searchFilters);
    // TODO: API 호출로 실제 검색 구현
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        차량 검색
      </Typography>
      
      {/* 검색 필터 */}
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          검색 조건
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>제조사</InputLabel>
              <Select
                value={searchFilters.make}
                onChange={(e) => handleFilterChange('make', e.target.value)}
                label="제조사"
              >
                <MenuItem value="">전체</MenuItem>
                <MenuItem value="현대">현대</MenuItem>
                <MenuItem value="기아">기아</MenuItem>
                <MenuItem value="삼성">삼성</MenuItem>
                <MenuItem value="쌍용">쌍용</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              label="모델명"
              value={searchFilters.model}
              onChange={(e) => handleFilterChange('model', e.target.value)}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              type="number"
              label="최소 가격 (만원)"
              value={searchFilters.minPrice}
              onChange={(e) => handleFilterChange('minPrice', e.target.value)}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              type="number"
              label="최대 가격 (만원)"
              value={searchFilters.maxPrice}
              onChange={(e) => handleFilterChange('maxPrice', e.target.value)}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              type="number"
              label="최소 연식"
              value={searchFilters.minYear}
              onChange={(e) => handleFilterChange('minYear', e.target.value)}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              type="number"
              label="최대 연식"
              value={searchFilters.maxYear}
              onChange={(e) => handleFilterChange('maxYear', e.target.value)}
            />
          </Grid>
          <Grid item xs={12}>
            <Button
              variant="contained"
              startIcon={<SearchIcon />}
              onClick={handleSearch}
              size="large"
            >
              검색하기
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* 검색 결과 */}
      <Typography variant="h6" gutterBottom>
        검색 결과 ({vehicles.length}건)
      </Typography>
      <Grid container spacing={3}>
        {vehicles.map((vehicle) => (
          <Grid item xs={12} sm={6} md={4} key={vehicle.id}>
            <Card>
              <CardMedia
                component="img"
                height="200"
                image={vehicle.image}
                alt={`${vehicle.make} ${vehicle.model}`}
              />
              <CardContent>
                <Typography gutterBottom variant="h6">
                  {vehicle.make} {vehicle.model}
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Chip 
                    label={`${vehicle.year}년`} 
                    variant="outlined" 
                    size="small" 
                    sx={{ mr: 1 }}
                  />
                  <Chip 
                    label={`${vehicle.mileage.toLocaleString()}km`} 
                    variant="outlined" 
                    size="small" 
                  />
                </Box>
                <Typography variant="h6" color="primary">
                  {vehicle.price.toLocaleString()}만원
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {vehicle.details.color} • {vehicle.details.fuel}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default VehicleSearch;