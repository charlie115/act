import Tab from '@mui/material/Tab';

import { styled, alpha } from '@mui/material/styles';

export default styled(Tab)(({ theme }) => ({
  color: theme.palette.text.secondary,
  fontSize: theme.typography.body2.fontSize,
  fontWeight: theme.typography.fontWeightMedium,
  letterSpacing: '0.02em',
  minHeight: 48,
  opacity: 1,
  padding: theme.spacing(1.5, 2),
  textTransform: 'none',
  transition: theme.transitions.create(['color', 'background-color', 'opacity'], {
    duration: theme.transitions.duration.short,
  }),
  '&:hover': {
    color: theme.palette.text.primary,
    backgroundColor: alpha(theme.palette.primary?.main || '#007cff', 0.04),
  },
  '&.Mui-selected': {
    color: theme.palette.primary.main,
    fontWeight: theme.typography.fontWeightBold,
  },
  '&.Mui-disabled': {
    opacity: 0.5,
  },
  [theme.breakpoints.down('md')]: {
    fontSize: '0.875rem',
    minHeight: 40,
    padding: theme.spacing(1, 1.5),
  },
}));