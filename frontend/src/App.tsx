import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import HybridCarFinInterface from './components/HybridCarFinInterface';

// Create Material-UI theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2', // Blue theme for CarFin
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    h3: {
      fontWeight: 600,
      marginBottom: '1rem',
    },
    h6: {
      fontWeight: 500,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <HybridCarFinInterface />
    </ThemeProvider>
  );
}

export default App;