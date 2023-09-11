import { alpha } from '@mui/material/styles';

export default {
  MuiButton: {
    styleOverrides: {
      contained: ({ theme }) => ({
        '&:disabled': {
          backgroundColor: theme.palette.grey['700'],
          opacity: 0.5,
        },
      }),
      outlined: ({ ownerState, theme }) => ({
        backgroundColor:
          theme.palette.mode === 'dark'
            ? 'transparent'
            : alpha(theme.palette[ownerState.color].main, 0.15),
        color:
          theme.palette.mode === 'dark'
            ? theme.palette[ownerState.color].main
            : theme.palette.grey['700'],
        fontWeight: 700,
        '&:disabled': {
          borderColor: theme.palette.grey['700'],
          color: theme.palette.grey['700'],
          opacity: 0.5,
        },
      }),
      // root: { minWidth: 'max-content', whiteSpace: 'nowrap' },
    },
  },
  MuiToggleButton: {
    styleOverrides: {
      root: ({ ownerState, theme }) => ({
        color: theme.palette[ownerState.color].main,
        '&:disabled': {
          borderColor: theme.palette.grey['700'],
          color: theme.palette.grey['700'],
          opacity: 0.5,
        },
        '&.Mui-selected': {
          backgroundColor: alpha(theme.palette.primary.main, 0.2),
          color: theme.palette.text.main,
          fontWeight: 700,
        },
      }),
    },
  },
};
