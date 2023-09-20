import React, { useCallback, useEffect, useMemo, useRef } from 'react';

import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';

import { createChart, ColorType } from 'lightweight-charts';

import { DateTime } from 'luxon';
import sortBy from 'lodash/sortBy';

import { useTheme } from '@mui/material/styles';

export default function LightWeightKLineChart({ data }) {
  const theme = useTheme();

  const chartRef = useRef();
  const chartContainerRef = useRef();

  const candlestickSeriesRef = useRef();

  // const chartData = useMemo(() => {
  //   const left = Object.values(data).map((item) => ({
  //     time: item.datetime_now,
  //     open: item.tp_open,
  //     high: item.tp_high,
  //     low: item.tp_low,
  //     close: item.tp_close,
  //   }));
  //   return { left: sortBy(left ?? [], 'datetime_now') };
  // }, [data]);

  const onVisibleLogicalRangeChange = useCallback((newLogicalRange) => {
    console.log('newLogicalRange: ', newLogicalRange);
  }, []);

  useEffect(() => {
    chartRef.current = createChart(chartContainerRef.current, {
      // leftPriceScale: { visible: true },
      // rightPriceScale: { visible: true },
      layout: {
        background: {
          type: ColorType.Solid,
          color: theme.palette.background.paper,
        },
        textColor: theme.palette.text.main,
      },
      localization: {
        timeFormatter: (time) => DateTime.fromMillis(time).toFormat('HH:mm:ss'),
      },
      crosshair: { mode: 0 },
      width: chartContainerRef.current.clientWidth,
      height: 300,
    });
    chartRef.current.timeScale().applyOptions({
      tickMarkFormatter: (time) =>
        DateTime.fromMillis(time).toFormat('HH:mm:ss'),
    });
    chartRef.current
      .timeScale()
      .subscribeVisibleLogicalRangeChange(onVisibleLogicalRangeChange);
    candlestickSeriesRef.current = chartRef.current.addCandlestickSeries({
      // priceScaleId: 'left',
      upColor: theme.palette.success.main,
      wickUpColor: theme.palette.success.main,
      downColor: theme.palette.error.main,
      wickDownColor: theme.palette.error.main,
      // lineWidth: 2,
      // priceFormat: { precision: 2, minMove: 0.01 },
      title: 'tp',
    });
    if (data)
      candlestickSeriesRef.current.setData([
        {
          time: data.datetime_now,
          open: data.tp_open,
          high: data.tp_high,
          low: data.tp_low,
          close: data.tp_close,
        },
      ]);
  }, []);

  useEffect(() => {
    console.log('data: ', data);

    // candlestickSeriesRef.current.setData(chartData.left);
    // const length = chartData?.left?.length;
    // if (length > 0) {
    //   candlestickSeriesRef.current.update(chartData?.left[length - 1]);
    //   chartRef.current.timeScale().fitContent();
    // }
    if (data)
      candlestickSeriesRef.current.update({
        time: data.datetime_now,
        open: data.tp_open,
        high: data.tp_high,
        low: data.tp_low,
        close: data.tp_close,
      });
    chartRef.current.timeScale().fitContent();
  }, [data]);

  return (
    <Box component={Paper}>
      <div ref={chartContainerRef} />
    </Box>
  );
}
