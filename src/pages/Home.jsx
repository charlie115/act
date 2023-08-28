import React from 'react';

import { useLocation } from 'react-router-dom';

import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Paper from '@mui/material/Paper';

import { alpha, styled } from '@mui/material/styles';

// import CoinsSelector from 'components/CoinsSelector';
import CoinsTable from 'components/CoinsTable';

import RealTimePriceChart from 'components/charts/RealTimePriceChart';

const SectionContainer = styled(Paper)(() => ({
  minHeight: 400,
  textAlign: 'center',
}));

function Home() {
  const location = useLocation();

  // const { data: prices } = useGetPriceWebsocketDataQuery({
  //   location: location.pathname,
  // });

  return (
    <Box>
      <Grid container spacing={2}>
        <Box item md={3} component={Grid} display={{ sm: 'none', md: 'block' }}>
          <SectionContainer>AD???</SectionContainer>
        </Box>
        <Grid item sm={12} md={6}>
          {/* <CoinsSelector /> */}
          <SectionContainer sx={{ p: 1 }}>
            <CoinsTable id="home-coins-table" />
            <RealTimePriceChart />
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
