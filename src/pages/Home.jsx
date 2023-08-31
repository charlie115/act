import React, { useEffect } from 'react';

import { useLocation } from 'react-router-dom';

import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Paper from '@mui/material/Paper';

import { styled } from '@mui/material/styles';

import { useGetKpWebsocketDataQuery } from 'redux/api/websocket';

import CoinsTable from 'components/CoinsTable';
import TVTickerWidget from 'components/trading_view/TVTickerWidget';

const SectionContainer = styled(Paper)(() => ({
  minHeight: 400,
  textAlign: 'center',
}));

function Home() {
  const location = useLocation();

  const { data } = useGetKpWebsocketDataQuery({ page: location.pathname });

  return (
    <Box>
      <TVTickerWidget />
      <Grid container spacing={1.25}>
        <Box item md={2} component={Grid} display={{ sm: 'none', md: 'block' }}>
          <SectionContainer>AD???</SectionContainer>
        </Box>
        <Grid item sm={12} md={8}>
          <SectionContainer sx={{ p: 1 }}>
            <CoinsTable data={data?.coinData} priceData={data?.coinPriceData} />
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
