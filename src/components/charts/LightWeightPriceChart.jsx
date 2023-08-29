import React, { useEffect, useMemo, useRef, useState } from 'react';

import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';

import { createChart, ColorType } from 'lightweight-charts';

import { DateTime } from 'luxon';
import sortBy from 'lodash/sortBy';

import { useTheme } from '@mui/material/styles';

function LightWeightPriceChart({ data }) {
  const theme = useTheme();

  const chartRef = useRef();
  const chartContainerRef = useRef();
  const kimpPriceSeriesRef = useRef();
  const binancePriceSeriesRef = useRef();

  useEffect(() => {
    chartRef.current = createChart(chartContainerRef.current, {
      leftPriceScale: { visible: true },
      rightPriceScale: { visible: true },
      layout: {
        background: {
          type: ColorType.Solid,
          color: theme.palette.background.paper,
        },
        textColor: theme.palette.text.main,
      },
      crosshair: { mode: 0 },
      width: chartContainerRef.current.clientWidth,
      height: 300,
    });
    chartRef.current.timeScale().applyOptions({
      tickMarkFormatter: (time) =>
        DateTime.fromMillis(time).toFormat('HH:mm:ss'),
    });
    kimpPriceSeriesRef.current = chartRef.current.addLineSeries({
      color: '#2962FF',
      lineWidth: 2,
      priceFormat: {
        minMove: 1,
        precision: 0,
      },
    });
    binancePriceSeriesRef.current = chartRef.current.addLineSeries({
      priceScaleId: 'left',
      color: '#fd6396',
      lineWidth: 2,
      priceFormat: {
        minMove: 1,
        precision: 0,
      },
    });
  }, []);

  useEffect(() => {
    const kimpData = data?.map((coin) => ({
      time: coin.time,
      value: coin.tp_kimp,
    }));
    const binanceData = data?.map((coin) => ({
      time: coin.time,
      value: coin.binance_ask_price,
    }));

    kimpPriceSeriesRef.current.setData(sortBy(kimpData ?? [], 'time'));
    binancePriceSeriesRef.current.setData(sortBy(binanceData ?? [], 'time'));

    chartRef.current.timeScale().fitContent();
  }, [data]);

  useEffect(() => {
    chartRef.current.applyOptions({
      layout: {
        background: {
          type: ColorType.Solid,
          color: theme.palette.background.paper,
        },
        textColor: theme.palette.text.main,
      },
    });
  }, [theme.palette.mode]);

  return (
    <Box component={Paper}>
      <div ref={chartContainerRef} />
    </Box>
  );
}

export default React.memo(LightWeightPriceChart);
