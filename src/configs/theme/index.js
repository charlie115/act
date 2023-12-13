import { createTheme } from '@mui/material/styles';

import colors, { darkColors } from './colors';
import components from './components';

// https://github.com/app-generator/react-soft-ui-dashboard/tree/main/src/assets/theme

export const SIDEBAR_WIDTH =
  window.innerWidth > 400 ? window.innerWidth * 0.27 : window.innerWidth - 60;

export const darkTheme = createTheme({
  components,
  palette: { ...darkColors },
  typography: { fontSize: 12 },
  breakpoints: {
    values: {
      xs: 0,
      sm: 640,
      md: 700,
      lg: 1024,
      xl: 1200,
      xxl: 1500,
    },
  },
});

export default createTheme({
  components,
  palette: { ...colors },
  typography: { fontSize: 12 },
  breakpoints: {
    values: {
      xs: 0,
      sm: 640,
      md: 700,
      lg: 1024,
      xl: 1200,
      xxl: 1500,
    },
  },
});
