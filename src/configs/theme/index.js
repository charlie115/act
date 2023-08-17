import { createTheme } from '@mui/material/styles';

import colors from './colors';
import components from './components';

// https://github.com/app-generator/react-soft-ui-dashboard/tree/main/src/assets/theme

export const SIDEBAR_WIDTH =
  window.innerWidth > 400 ? window.innerWidth * 0.27 : window.innerWidth - 60;

export const darkTheme = createTheme({
  components,
  palette: {
    ...colors,
    background: {
      default: '#121212',
      paper: '#121212',
    },
    divider: 'rgba(255, 255, 255, 0.12)',
    mode: 'dark',
  },
});

export default createTheme({
  components,
  palette: { ...colors },
});
