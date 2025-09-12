import React, { useState } from 'react';
import { 
  ThemeProvider, 
  createTheme, 
  CssBaseline, 
  AppBar, 
  Toolbar, 
  Typography, 
  Container, 
  Box,
  Tabs,
  Tab
} from '@mui/material';
import DirectionsCarIcon from '@mui/icons-material/DirectionsCar';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import RecommendIcon from '@mui/icons-material/Recommend';

import VehicleSearch from './components/VehicleSearch';
import UserProfile from './components/UserProfile';
import Recommendations from './components/Recommendations';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function App() {
  const [currentTab, setCurrentTab] = useState(0);

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppBar position="static">
        <Toolbar>
          <DirectionsCarIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            CarFin - AI 차량 추천 플랫폼
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 2 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={currentTab} onChange={handleTabChange} aria-label="CarFin 탭">
            <Tab 
              icon={<DirectionsCarIcon />} 
              label="차량 검색" 
              id="tab-0"
              aria-controls="tabpanel-0"
            />
            <Tab 
              icon={<AccountCircleIcon />} 
              label="사용자 프로필" 
              id="tab-1"
              aria-controls="tabpanel-1"
            />
            <Tab 
              icon={<RecommendIcon />} 
              label="AI 추천" 
              id="tab-2"
              aria-controls="tabpanel-2"
            />
          </Tabs>
        </Box>

        <TabPanel value={currentTab} index={0}>
          <VehicleSearch />
        </TabPanel>
        <TabPanel value={currentTab} index={1}>
          <UserProfile />
        </TabPanel>
        <TabPanel value={currentTab} index={2}>
          <Recommendations />
        </TabPanel>
      </Container>
    </ThemeProvider>
  );
}

export default App;