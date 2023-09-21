import React, { useMemo } from 'react';

import { useLocation } from 'react-router-dom';

import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';

import { useGetKpWebsocketDataQuery } from 'redux/api/websocket';

import RealTimeCoinsTable from 'components/RealTimeCoinsTable';

function Home() {
  // const { data } = useGetKpWebsocketDataQuery();

  // const coinData = useMemo(
  //   () =>
  //     data?.coinList.map((coin) => ({
  //       ...data?.coinRealTimeData?.[coin],
  //       icon: coinicons[`${coin}.png`]
  //         ? require(`assets/icons/coinicon/${coin}.png`)
  //         : null,
  //     })),
  //   [data?.coinRealTimeData]
  // );

  return (
    <Box>
      <RealTimeCoinsTable
      // realTimeData={coinData || []}
      // seriesData={data?.coinSeriesData}
      />
    </Box>
  );
}

export default Home;
