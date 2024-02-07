import Tabs from '@mui/material/Tabs';

import { styled } from '@mui/material/styles';

export default styled(Tabs)(({ theme }) => ({
  borderBottomStyle: '1',
  borderBottomWidth: 1,
  borderColor: theme.palette.divider,
  marginBottom: 8,
  '& .MuiTabs-indicator': {
    backgroundColor: theme.palette.text.main,
    height: '1px',
  },
}));
