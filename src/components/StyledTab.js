import Tab from '@mui/material/Tab';

import { styled } from '@mui/material/styles';

export default styled(Tab)(({ theme }) => ({
  color: theme.palette.text.main,
  opacity: 0.7,
  textTransform: 'none',
  '&.Mui-selected': {
    color: theme.palette.text.main,
    fontWeight: 700,
    opacity: 1,
  },
}));
