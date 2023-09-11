import React, { useMemo } from 'react';

import { useLocation } from 'react-router-dom';

import Box from '@mui/material/Box';

import { useGetKpWebsocketDataQuery } from 'redux/api/websocket';

import ArbitrageTable from 'components/ArbitrageTable';

import { coinicons } from 'assets/exports';

export default function Arbitrage() {
  const location = useLocation();

  const { data } = useGetKpWebsocketDataQuery();

  const coinData = useMemo(
    () =>
      data?.coinList.map((coin) => ({
        ...data?.coinRealTimeData?.[coin],
        icon: coinicons[`${coin}.png`]
          ? require(`assets/icons/coinicon/${coin}.png`)
          : null,
      })),
    [data?.coinRealTimeData]
  );

  return (
    <Box>
      <ArbitrageTable data={coinData || []} />
    </Box>
  );
}
