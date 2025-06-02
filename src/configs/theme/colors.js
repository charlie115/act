import { cyan, lightGreen, purple, teal } from '@mui/material/colors';

// Sophisticated color palette with full scales
const colors = {
  cyan,
  lightGreen,
  purple,
  teal,

  // Enhanced background colors with subtle variations
  background: {
    default: '#fafbfc',
    paper: '#ffffff',
    elevated: '#ffffff',
    backdrop: 'rgba(0, 0, 0, 0.5)',
    overlay: 'rgba(255, 255, 255, 0.95)',
  },

  divider: 'rgba(0, 0, 0, 0.04)',

  text: { 
    main: '#1a1d29',
    primary: '#1a1d29',
    secondary: '#64748b',
    disabled: '#94a3b8',
    hint: '#cbd5e1',
  },

  transparent: { main: 'transparent' },

  white: { main: '#ffffff' },

  black: { light: '#212529', main: '#000000' },

  // Modern accent color with scale
  accent: { 
    50: '#fffef7',
    100: '#fffce0',
    200: '#fff8c4',
    300: '#fff59d',
    400: '#fff176',
    500: '#ffeb3b',
    main: '#fad532',
    600: '#fbc02d',
    700: '#f9a825',
    800: '#f57f17',
    900: '#f57c00',
  },

  // Sophisticated primary blue scale
  primary: { 
    50: '#e6f3ff',
    100: '#b3d9ff',
    200: '#80bfff',
    300: '#4da6ff',
    400: '#1a8cff',
    main: '#007cff',
    600: '#0066d9',
    700: '#0052b3',
    800: '#003d8c',
    900: '#002966',
    contrastText: '#ffffff',
  },

  // Refined secondary scale
  secondary: { 
    50: '#f8fafc',
    100: '#f1f5f9',
    200: '#e2e8f0',
    300: '#cbd5e1',
    400: '#94a3b8',
    main: '#64748b',
    600: '#475569',
    700: '#334155',
    800: '#1e293b',
    900: '#0f172a',
  },

  info: { 
    50: '#e6f9ff',
    100: '#b3edff',
    200: '#80e1ff',
    300: '#4dd5ff',
    400: '#1ac9ff',
    main: '#00bbff',
    600: '#00a3e6',
    700: '#008acc',
    800: '#0072b3',
    900: '#005999',
  },

  success: { 
    50: '#e8f9f4',
    100: '#c3f0e3',
    200: '#9de6d1',
    300: '#77dcbf',
    400: '#51d2ad',
    main: '#25C196',
    600: '#20a884',
    700: '#1b8f71',
    800: '#16765e',
    900: '#115d4b',
    light: '#7afa90',
    dark: '#00543d',
  },

  warning: { 
    50: '#fff8e1',
    100: '#ffecb3',
    200: '#ffe082',
    300: '#ffd54f',
    400: '#ffca28',
    main: '#faa12d',
    600: '#fb8c00',
    700: '#f57c00',
    800: '#ef6c00',
    900: '#e65100',
    light: '#ffc65f',
  },

  error: { 
    50: '#ffebee',
    100: '#ffcdd2',
    200: '#ef9a9a',
    300: '#e57373',
    400: '#ef5350',
    main: '#ff0d45',
    600: '#e53935',
    700: '#d32f2f',
    800: '#c62828',
    900: '#b71c1c',
    light: '#ed5588',
  },

  light: { main: '#f8fafc' },

  dark: { light: '#1a1d29', main: '#0f111a' },

  // Modern grey scale
  grey: {
    50: '#f8fafc',
    100: '#f1f5f9',
    200: '#e2e8f0',
    300: '#cbd5e1',
    400: '#94a3b8',
    500: '#64748b',
    600: '#475569',
    700: '#334155',
    800: '#1e293b',
    900: '#0f172a',
  },

  // Enhanced gradients for modern look
  gradients: {
    primary: 'linear-gradient(135deg, #007cff 0%, #0066d9 100%)',
    primaryRadial: 'radial-gradient(circle at top left, #4da6ff, #007cff)',
    accent: 'linear-gradient(135deg, #fad532 0%, #f9a825 100%)',
    success: 'linear-gradient(135deg, #51d2ad 0%, #25C196 100%)',
    error: 'linear-gradient(135deg, #ff0d45 0%, #d32f2f 100%)',
    info: 'linear-gradient(135deg, #00bbff 0%, #0072b3 100%)',
    dark: 'linear-gradient(135deg, #1a1d29 0%, #0f111a 100%)',
    mesh: 'radial-gradient(at 40% 20%, #4da6ff 0px, transparent 50%), radial-gradient(at 80% 0%, #fad532 0px, transparent 50%), radial-gradient(at 40% 50%, #51d2ad 0px, transparent 50%)',
    glass: 'linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%)',
  },

  // Social media colors remain the same
  facebook: {
    main: '#3b5998',
    dark: '#344e86',
  },

  twitter: {
    main: '#55acee',
    dark: '#3ea1ec',
  },

  instagram: {
    main: '#125688',
    dark: '#0e456d',
  },

  linkedin: {
    main: '#0077b5',
    dark: '#00669c',
  },

  pinterest: {
    main: '#cc2127',
    dark: '#b21d22',
  },

  youtube: {
    main: '#e52d27',
    dark: '#d41f1a',
  },

  vimeo: {
    main: '#1ab7ea',
    dark: '#13a3d2',
  },

  slack: {
    main: '#3aaf85',
    dark: '#329874',
  },

  dribbble: {
    main: '#ea4c89',
    dark: '#e73177',
  },

  github: {
    main: '#24292e',
    dark: '#171a1d',
  },

  reddit: {
    main: '#ff4500',
    dark: '#e03d00',
  },

  telegram: {
    main: '#4AA3E2',
  },

  tumblr: {
    main: '#35465c',
    dark: '#2a3749',
  },

  // UI element colors
  inputBorderColor: 'rgba(203, 213, 225, 0.5)',
  inputBorderColorHover: 'rgba(148, 163, 184, 0.5)',
  inputBorderColorFocus: '#007cff',

  tabs: {
    indicator: { boxShadow: 'rgba(0, 124, 255, 0.2)' },
  },

  // Elevation shadows for depth
  shadows: {
    small: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
    medium: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    large: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
  },
};

// Dark theme colors with better contrast
export const darkColors = {
  ...colors,
  background: { 
    default: '#0a0b0f',
    paper: '#141821',
    elevated: '#1a1f2e',
    backdrop: 'rgba(0, 0, 0, 0.8)',
    overlay: 'rgba(20, 24, 33, 0.95)',
  },
  text: { 
    main: '#f8fafc',
    primary: '#f8fafc',
    secondary: '#cbd5e1',
    disabled: '#64748b',
    hint: '#475569',
  },
  divider: 'rgba(255, 255, 255, 0.08)',
  mode: 'dark',
  
  // Adjusted input colors for dark mode
  inputBorderColor: 'rgba(100, 116, 139, 0.3)',
  inputBorderColorHover: 'rgba(148, 163, 184, 0.4)',
  inputBorderColorFocus: '#4da6ff',
  
  // Dark mode shadows
  shadows: {
    small: '0 1px 3px 0 rgba(0, 0, 0, 0.3), 0 1px 2px 0 rgba(0, 0, 0, 0.2)',
    medium: '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2)',
    large: '0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.2)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2)',
    inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.2)',
  },
};

export default colors;