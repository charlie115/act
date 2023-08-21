import React from 'react';

import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Paper from '@mui/material/Paper';

import { styled } from '@mui/material/styles';

import CoinsSelector from 'components/CoinsSelector';
import TVRealTimeChart from 'components/trading_view/TVRealTimeChart';

const SectionContainer = styled(Paper)(({ theme }) => ({
  textAlign: 'center',
  minHeight: 800,
}));

function Home() {
  return (
    <Box>
      <Grid container spacing={2}>
        <Box item md={3} component={Grid} display={{ sm: 'none', md: 'block' }}>
          <SectionContainer>AD???</SectionContainer>
        </Box>
        <Grid item sm={12} md={6}>
          {/* <CoinsSelector /> */}
          <SectionContainer>
            {/* <TVRealTimeChart containerId="chart-1" symbol="BINANCE:SUIUSDT" /> */}
          </SectionContainer>
        </Grid>
        <Box item md={3} component={Grid} display={{ sm: 'none', md: 'block' }}>
          <SectionContainer>AD???</SectionContainer>
        </Box>
      </Grid>
    </Box>
  );
}

export default Home;
