import Tabs from '@mui/material/Tabs';

import { styled } from '@mui/material/styles';

export default styled(Tabs)(({ theme }) => ({
  '& .MuiTabs-indicator': {
    backgroundColor: theme.palette.text.main,
    height: '1px',
  },
}));
