import React, { useEffect, useMemo, useRef } from 'react';

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
  const leftPriceSeriesRef = useRef();
  const rightPriceSeriesRef = useRef();

  const chartData = useMemo(() => {
    const leftData = data?.map((coin) => ({
      time: coin.time,
      value: coin.trade_price,
    }));
    const rightData = data?.map((coin) => ({
      time: coin.time,
      value: coin.tp_kimp,
    }));

    return {
      left: sortBy(leftData ?? [], 'time'),
      right: sortBy(rightData ?? [], 'time'),
    };
  }, [data]);

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
      localization: {
        timeFormatter: (time) =>
          DateTime.fromMillis(time).toFormat('DD HH:mm:ss'),
      },
      crosshair: { mode: 0 },
      width: chartContainerRef.current.clientWidth,
      height: 300,
    });
    chartRef.current.timeScale().applyOptions({
      tickMarkFormatter: (time) =>
        DateTime.fromMillis(time).toFormat('HH:mm:ss'),
    });
    leftPriceSeriesRef.current = chartRef.current.addLineSeries({
      priceScaleId: 'left',
      color: '#fd6396',
      lineWidth: 2,
      priceFormat: { precision: 2, minMove: 0.01 },
      title: 'upbit?',
    });
    rightPriceSeriesRef.current = chartRef.current.addLineSeries({
      priceScaleId: 'right',
      color: '#2962FF',
      lineWidth: 2,
      priceFormat: { precision: 2, minMove: 0.01 },
      title: 'tp_kimp',
    });
    rightPriceSeriesRef.current.priceScale().applyOptions({
      autoScale: false,
      scaleMargins: { bottom: 0, top: 0.9 },
    });
  }, []);

  useEffect(() => {
    leftPriceSeriesRef.current.setData(chartData.left);
    rightPriceSeriesRef.current.setData(chartData.right);
    chartRef.current.timeScale().fitContent();
  }, [chartData]);

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
