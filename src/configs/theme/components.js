import colors from './colors';

export default {
  MuiButton: {
    styleOverrides: {
      contained: {
        '&:disabled': {
          backgroundColor: colors.grey['700'],
          opacity: 0.5,
        },
      },
      outlined: {
        color: colors.white.main,
        '&:disabled': {
          borderColor: colors.grey['700'],
          color: colors.grey['700'],
          opacity: 0.5,
        },
      },
    },
  },
};
