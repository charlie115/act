import Tabs from '@mui/material/Tabs';

import { styled } from '@mui/material/styles';

export default styled(Tabs)(({ theme }) => ({
  borderBottom: `1px solid ${theme.palette.divider}`,
  marginBottom: theme.spacing(2),
  minHeight: 48,
  '& .MuiTabs-indicator': {
    backgroundColor: theme.palette.primary.main,
    height: 3,
    borderRadius: '3px 3px 0 0',
    transition: theme.transitions.create(['all'], {
      duration: theme.transitions.duration.short,
    }),
  },
  '& .MuiTabs-flexContainer': {
    gap: theme.spacing(0.5),
  },
  '& .MuiTabs-scrollButtons': {
    color: theme.palette.text.secondary,
    '&.Mui-disabled': {
      opacity: 0.3,
    },
  },
}));