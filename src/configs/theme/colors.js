import { cyan, lightGreen, purple, teal } from '@mui/material/colors';

const colors = {
  cyan,
  lightGreen,
  purple,
  teal,

  background: {
    default: '#f7fbfc',
    paper: '#fff',
  },

  divider: 'rgba(0, 0, 0, 0.12)',

  text: { main: '#373a48' },

  transparent: { main: 'transparent' },

  white: { main: '#ffffff' },

  black: { light: '#212529', main: '#000000' },

  accent: { light: '#fce174', main: '#fad532' },

  primary: { main: '#007cff', light: '#44b0fd' },

  secondary: { main: '#90a4ae' },

  info: { main: '#00bbff' },

  success: { main: '#25C196', light: '#7afa90', dark: '#00543d' },

  warning: { light: '#ffc65f', main: '#faa12d' },

  error: { main: '#ff0d45', light: '#ed5588' },

  light: { main: '#f0f2f5' },

  dark: { light: '#0e1114', main: '#121212' },

  grey: {
    100: '#cfd8dc',
    200: '#b0bec5',
    300: '#90a4ae',
    400: '#78909c',
    500: '#607d8b',
    600: '#546e7a',
    700: '#455a64',
    800: '#37474f',
    900: '#263238',
  },

  gradients: {
    primary: {
      main: '#007cff',
      state: '#6A6EEC',
    },

    secondary: {
      main: '#a8aabc',
      state: '#495361',
    },

    info: {
      main: '#00bbff',
      state: '#00c4f0',
    },

    success: {
      main: '#25C196',
      state: '#1b906f',
    },

    warning: {
      main: '#ffc65f',
      state: '#FB8C00',
    },

    error: {
      main: '#ff0d45',
      state: '#fd2f5e',
    },

    light: {
      main: '#EBEFF4',
      state: '#CED4DA',
    },

    dark: {
      main: '#121212',
      state: '#42424a',
    },
  },

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

  inputBorderColor: '#d2d6da',

  tabs: {
    indicator: { boxShadow: '#ddd' },
  },
};

export const darkColors = {
  ...colors,
  background: { default: '#000000', paper: '#0e1114' },
  text: { main: '#ffffff' },
  divider: 'rgba(255, 255, 255, 0.12)',
  mode: 'dark',
};

export default colors;
