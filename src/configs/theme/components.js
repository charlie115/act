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
      outlined: ({ ownerState, theme }) => ({
        color: theme.palette[ownerState.color].main,
        '&:disabled': {
          borderColor: colors.grey['700'],
          color: colors.grey['700'],
          opacity: 0.5,
        },
      }),
    },
  },
  MuiToggleButton: {
    styleOverrides: {
      root: ({ ownerState, theme }) => ({
        color: theme.palette[ownerState.color].main,
        '&:disabled': {
          borderColor: colors.grey['700'],
          color: colors.grey['700'],
          opacity: 0.5,
        },
      }),
    },
  },
};
