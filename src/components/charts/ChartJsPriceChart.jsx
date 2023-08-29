import React, { useEffect, useMemo, useRef, useState } from 'react';

import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import { Line } from 'react-chartjs-2';

import { DateTime } from 'luxon';
import sortBy from 'lodash/sortBy';

import { useTheme } from '@mui/material/styles';

export const DEFAULT_OPTIONS = {
  // spanGaps: 1000 * 60 * 60 * 24 * 2, // 2 days
  responsive: true,
  interaction: {
    mode: 'index',
    intersect: true,
  },
  stacked: false,
  plugins: {
    title: {
      display: true,
      text: 'Chart.js Line Chart - Multi Axis',
    },
  },
  scales: {
    x: {
      type: 'time',
      time: { tooltipFormat: 'HH:mm:ss', unit: 'second' },
      ticks: { autoSkip: true },
    },
    y: {
      type: 'linear',
      display: true,
      position: 'left',
    },
    y1: {
      type: 'linear',
      display: true,
      position: 'right',
      grid: {
        drawOnChartArea: false,
      },
    },
  },
};

function ChartJsPriceChart({ data }) {
  const chartRef = useRef();

  const theme = useTheme();

  const chartData = useMemo(
    () => ({
      // labels: data?.map((datum) => {
      //   const coin = datum.find((item) => item.symbol.includes(symbol));
      //   return coin.timestamp; // DateTime.fromMillis(coin.timestamp).toFormat('HH:mm:ss');
      // }),
      datasets: [
        {
          label: 'tp_kimp',
          data: data?.map((coin) => ({ x: coin.time, y: coin.tp_kimp })),
          backgroundColor: 'rgba(255, 99, 132, 0.5)',
          borderColor: 'rgb(255, 99, 132)',
          yAxisID: 'y1',
        },
        {
          label: 'binance???',
          data: data?.map((coin) => ({
            x: coin.time,
            y: coin.trade_price,
          })),
          backgroundColor: 'rgba(94, 118, 255, 0.5)',
          borderColor: 'rgb(94, 118, 255)',
          yAxisID: 'y',
        },
      ],
    }),
    [data]
  );

  return (
    <Box component={Paper} sx={{ bgcolor: theme.palette.background.default }}>
      <Line ref={chartRef} options={DEFAULT_OPTIONS} data={chartData} />
    </Box>
  );
}

export default React.memo(ChartJsPriceChart);
