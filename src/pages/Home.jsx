import React, { useEffect } from 'react';

import { useLocation } from 'react-router-dom';

import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Paper from '@mui/material/Paper';

import { alpha, styled } from '@mui/material/styles';

import { useGetKpWebsocketDataQuery } from 'redux/api/websocket';

// import CoinsSelector from 'components/CoinsSelector';
import CoinsTable from 'components/CoinsTable';

import ChartJsPriceChart from 'components/charts/ChartJsPriceChart';
import LightWeightPriceChart from 'components/charts/LightWeightPriceChart';
import RealTimePriceChart from 'components/charts/RealTimePriceChart';

const SectionContainer = styled(Paper)(() => ({
  minHeight: 400,
  textAlign: 'center',
}));

function Home() {
  const location = useLocation();

  const { data } = useGetKpWebsocketDataQuery({ page: location.pathname });

  return (
    <Box>
      <Grid container spacing={2}>
        <Box item md={2} component={Grid} display={{ sm: 'none', md: 'block' }}>
          <SectionContainer>AD???</SectionContainer>
        </Box>
        <Grid item sm={12} md={8}>
          {/* <CoinsSelector /> */}
          <SectionContainer sx={{ p: 1 }}>
            <CoinsTable data={data?.coinData} priceData={data?.coinPriceData} />
            {/* <ChartJsPriceChart data={data?.prices} symbol="SUI" /> */}
            {/* <LightWeightPriceChart data={data?.prices} symbol="SUI" /> */}
            {/* <RealTimePriceChart data={data?.prices} symbol="SUI" /> */}
            {/* <TVRealTimeChart containerId="chart-1" symbol="BINANCE:SUIUSDT" /> */}
          </SectionContainer>
        </Grid>
        <Box item md={2} component={Grid} display={{ sm: 'none', md: 'block' }}>
          <SectionContainer>AD???</SectionContainer>
        </Box>
      </Grid>
    </Box>
  );
}

export default Home;
