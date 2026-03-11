import { createTheme } from '@mui/material/styles';

import colors, { darkColors } from './colors';
import components from './components';

// https://github.com/app-generator/react-soft-ui-dashboard/tree/main/src/assets/theme

// Responsive sidebar width calculation
export const SIDEBAR_WIDTH =
  window.innerWidth > 400 ? Math.min(window.innerWidth * 0.27, 320) : window.innerWidth - 60;

// Typography configuration with modern scale
const typography = {
  fontFamily: [
    'Inter',
    '-apple-system',
    'BlinkMacSystemFont',
    '"Segoe UI"',
    'Roboto',
    '"Helvetica Neue"',
    'Arial',
    'sans-serif',
    '"Apple Color Emoji"',
    '"Segoe UI Emoji"',
    '"Segoe UI Symbol"',
  ].join(','),
  fontSize: 14, // Base font size increased from 12px
  fontWeightLight: 300,
  fontWeightRegular: 400,
  fontWeightMedium: 500,
  fontWeightBold: 700,
  h1: {
    fontSize: '3rem',
    fontWeight: 700,
    lineHeight: 1.2,
    letterSpacing: '-0.02em',
    '@media (max-width:600px)': {
      fontSize: '2.25rem',
    },
  },
  h2: {
    fontSize: '2.25rem',
    fontWeight: 700,
    lineHeight: 1.3,
    letterSpacing: '-0.01em',
    '@media (max-width:600px)': {
      fontSize: '1.875rem',
    },
  },
  h3: {
    fontSize: '1.875rem',
    fontWeight: 600,
    lineHeight: 1.375,
    letterSpacing: '-0.01em',
    '@media (max-width:600px)': {
      fontSize: '1.5rem',
    },
  },
  h4: {
    fontSize: '1.5rem',
    fontWeight: 600,
    lineHeight: 1.375,
    '@media (max-width:600px)': {
      fontSize: '1.25rem',
    },
  },
  h5: {
    fontSize: '1.25rem',
    fontWeight: 600,
    lineHeight: 1.375,
    '@media (max-width:600px)': {
      fontSize: '1.125rem',
    },
  },
  h6: {
    fontSize: '1.125rem',
    fontWeight: 600,
    lineHeight: 1.375,
    '@media (max-width:600px)': {
      fontSize: '1rem',
    },
  },
  subtitle1: {
    fontSize: '1rem',
    fontWeight: 500,
    lineHeight: 1.5,
    letterSpacing: '0.01em',
  },
  subtitle2: {
    fontSize: '0.875rem',
    fontWeight: 500,
    lineHeight: 1.5,
    letterSpacing: '0.01em',
  },
  body1: {
    fontSize: '1rem',
    fontWeight: 400,
    lineHeight: 1.6,
    letterSpacing: '0.01em',
    '@media (max-width:600px)': {
      fontSize: '0.875rem',
      lineHeight: 1.5,
    },
  },
  body2: {
    fontSize: '0.875rem',
    fontWeight: 400,
    lineHeight: 1.6,
    letterSpacing: '0.01em',
  },
  button: {
    fontSize: '0.8125rem', // 13px - Reduced from 14px
    fontWeight: 600,
    lineHeight: 1.75,
    letterSpacing: '0.02em',
    textTransform: 'none', // Remove uppercase transformation
  },
  caption: {
    fontSize: '0.75rem',
    fontWeight: 400,
    lineHeight: 1.66,
    letterSpacing: '0.02em',
  },
  overline: {
    fontSize: '0.75rem',
    fontWeight: 600,
    lineHeight: 2.5,
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
  },
};

// Spacing configuration (8px base)
const spacing = 8;

// Shape configuration
const shape = {
  borderRadius: 12, // Increased from default 4px for modern look
};

// Transition configuration
const transitions = {
  easing: {
    easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
    easeOut: 'cubic-bezier(0.0, 0, 0.2, 1)',
    easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
    sharp: 'cubic-bezier(0.4, 0, 0.6, 1)',
    // Modern easing for interactive elements
    bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
    decelerate: 'cubic-bezier(0, 0, 0.2, 1)',
    smooth: 'cubic-bezier(0.25, 0.1, 0.25, 1)',
  },
  duration: {
    shortest: 150,
    shorter: 200,
    short: 250,
    standard: 300,
    complex: 375,
    enteringScreen: 225,
    leavingScreen: 195,
    // Micro-interaction timings
    hover: 200,
    focus: 150,
    slide: 400,
  },
};

// Breakpoints configuration
const breakpoints = {
  values: {
    xs: 0,
    sm: 640,
    md: 768,
    lg: 1024,
    xl: 1280,
    xxl: 1536,
  },
};

// Z-index configuration
const zIndex = {
  appBar: 1100,
  drawer: 1200,
  modal: 1300,
  snackbar: 1400,
  tooltip: 1500,
};

// Create light theme
export default createTheme({
  components,
  palette: { 
    ...colors,
    mode: 'light',
  },
  typography,
  spacing,
  shape,
  transitions,
  breakpoints,
  zIndex,
  shadows: [
    'none',
    colors.shadows.small,
    colors.shadows.small,
    colors.shadows.medium,
    colors.shadows.medium,
    colors.shadows.medium,
    colors.shadows.large,
    colors.shadows.large,
    colors.shadows.large,
    colors.shadows.large,
    colors.shadows.xl,
    colors.shadows.xl,
    colors.shadows.xl,
    colors.shadows.xl,
    colors.shadows.xl,
    colors.shadows.xl,
    colors.shadows.xl,
    colors.shadows.xl,
    colors.shadows.xl,
    colors.shadows.xl,
    colors.shadows.xl,
    colors.shadows.xl,
    colors.shadows.xl,
    colors.shadows.xl,
    colors.shadows.xl,
  ],
});

// Create dark theme
export const darkTheme = createTheme({
  components,
  palette: { ...darkColors },
  typography,
  spacing,
  shape,
  transitions,
  breakpoints,
  zIndex,
  shadows: [
    'none',
    darkColors.shadows.small,
    darkColors.shadows.small,
    darkColors.shadows.medium,
    darkColors.shadows.medium,
    darkColors.shadows.medium,
    darkColors.shadows.large,
    darkColors.shadows.large,
    darkColors.shadows.large,
    darkColors.shadows.large,
    darkColors.shadows.xl,
    darkColors.shadows.xl,
    darkColors.shadows.xl,
    darkColors.shadows.xl,
    darkColors.shadows.xl,
    darkColors.shadows.xl,
    darkColors.shadows.xl,
    darkColors.shadows.xl,
    darkColors.shadows.xl,
    darkColors.shadows.xl,
    darkColors.shadows.xl,
    darkColors.shadows.xl,
    darkColors.shadows.xl,
    darkColors.shadows.xl,
    darkColors.shadows.xl,
  ],
});