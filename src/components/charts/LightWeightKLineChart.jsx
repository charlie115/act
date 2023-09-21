import React, {
  useCallback,
  useEffect,
  useState,
  useMemo,
  useRef,
} from 'react';

import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Grid from '@mui/material/Grid';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';

import StarIcon from '@mui/icons-material/Star';
import StarOutlineIcon from '@mui/icons-material/StarOutline';

import { createChart, ColorType, CrosshairMode } from 'lightweight-charts';

import { DateTime } from 'luxon';
import sortBy from 'lodash/sortBy';

import { useTranslation } from 'react-i18next';
import { alpha, useTheme } from '@mui/material/styles';

import { useGetWsCoinsQuery } from 'redux/api/websocket';

import formatIntlNumber from 'utils/formatIntlNumber';

import KLineDataSelector from 'components/KLineDataSelector';
import PeriodIntervalSelector from 'components/PeriodIntervalSelector';

const KLINE_DATA_KEY = 'tp';
const REALTIME_INTERVAL_KEY = '1T';

function LightWeightKLineChart({ coinData, selectedExchanges, initialData }) {
  const theme = useTheme();
  const { i18n, t } = useTranslation();

  const chartRef = useRef();
  const chartContainerRef = useRef();

  const candlestickSeriesRef = useRef();
  const lineSeriesRef = useRef();

  const [title, setTitle] = useState();

  const [selectedInterval, setSelectedInterval] = useState(
    REALTIME_INTERVAL_KEY
  );

  const [selectedKLineData, setSelectedKLineData] = useState(KLINE_DATA_KEY);

  const { data } = useGetWsCoinsQuery(
    { ...selectedExchanges, period: selectedInterval },
    { skip: !selectedExchanges }
  );

  const chartData = useMemo(() => {
    const value = data?.[coinData.base_asset];
    if (!value) return null;
    return {
      candlestick: {
        time: value.datetime_now,
        open: value[`${selectedKLineData}_open`],
        high: value[`${selectedKLineData}_high`],
        low: value[`${selectedKLineData}_low`],
        close: value[`${selectedKLineData}_close`],
      },
      line: { time: value.datetime_now, value: value.tp },
    };
  }, [data?.[coinData.base_asset], selectedKLineData]);

  const onVisibleLogicalRangeChange = useCallback((newLogicalRange) => {
    console.log('newLogicalRange: ', newLogicalRange);
  }, []);

  const onVisibleTimeRangeChange = useCallback((newTimeRange) => {
    // if (newTimeRange.from !== newTimeRange.to)
    //   chartRef.current.timeScale().fitContent();
  }, []);

  useEffect(() => {
    chartRef.current = createChart(chartContainerRef.current, {
      leftPriceScale: { visible: true },
      rightPriceScale: { visible: true },
      layout: {
        background: { color: theme.palette.background.paper },
        textColor: theme.palette.text.main,
      },
      grid: {
        vertLines: { color: alpha(theme.palette.grey['600'], 0.15) },
        horzLines: { color: alpha(theme.palette.grey['600'], 0.15) },
      },
      localization: {
        timeFormatter: (time) =>
          DateTime.fromMillis(time).toFormat('DD HH:mm:ss'),
      },
      crosshair: { mode: CrosshairMode.Normal },
      width: chartContainerRef.current.clientWidth,
      height: 300,
    });
    chartRef.current.priceScale('left').applyOptions({
      borderColor: alpha(theme.palette.secondary.main, 0.2),
    });
    chartRef.current.priceScale('right').applyOptions({
      borderColor: alpha(theme.palette.secondary.main, 0.2),
    });
    chartRef.current.timeScale().applyOptions({
      barSpacing: 10,
      borderColor: alpha(theme.palette.secondary.main, 0.2),
      rightOffset: 4,
      tickMarkFormatter: (time) =>
        DateTime.fromMillis(time).toFormat('HH:mm:ss'),
    });
    chartRef.current
      .timeScale()
      .subscribeVisibleLogicalRangeChange(onVisibleLogicalRangeChange);
    chartRef.current
      .timeScale()
      .subscribeVisibleTimeRangeChange(onVisibleTimeRangeChange);

    candlestickSeriesRef.current = chartRef.current.addCandlestickSeries({
      priceScaleId: 'right',
      downColor: theme.palette.error.main,
      upColor: theme.palette.success.main,
      wickDownColor: theme.palette.error.main,
      wickUpColor: theme.palette.success.main,
      priceFormat: { minMove: 0.01, precision: 2, type: 'percent' },
      title: t('Premium'),
    });
    lineSeriesRef.current = chartRef.current.addLineSeries({
      priceScaleId: 'left',
      color: theme.palette.accent.main,
      crosshairMarkerVisible: false,
      lastValueVisible: false,
      lineWidth: 1,
      priceFormat: { minMove: 0.01, precision: 2, type: 'price' },
      title: t('Price'),
    });
  }, []);

  useEffect(() => {
    const isDark = theme.palette.mode === 'dark';
    chartRef.current.applyOptions({
      layout: {
        background: { color: theme.palette.background.paper },
        textColor: theme.palette.text.main,
      },
      crosshair: {
        vertLine: {
          labelBackgroundColor: theme.palette.grey[isDark ? '800' : '100'],
        },
        horzLine: {
          labelBackgroundColor: theme.palette.grey[isDark ? '800' : '100'],
        },
      },
    });
  }, [theme.palette.mode]);

  useEffect(() => {
    candlestickSeriesRef.current.setData(initialData);
    lineSeriesRef.current.setData(initialData);
  }, [initialData, selectedInterval]);

  useEffect(() => {
    if (chartData) {
      candlestickSeriesRef.current.update(chartData.candlestick);
      lineSeriesRef.current.update(chartData.line);
    }
  }, [chartData]);

  useEffect(() => {
    candlestickSeriesRef?.current.applyOptions({
      title: `${
        selectedExchanges?.baseExchange.includes('UPBIT')
          ? t('KIMP')
          : t('Premium')
      } (${selectedKLineData.toUpperCase()})`,
    });
  }, [i18n.language, selectedExchanges, selectedKLineData]);

  useEffect(() => {
    const value = selectedExchanges?.baseExchange;
    setTitle(`${coinData.base_asset} / ${value?.split('/').pop()}`);
  }, [selectedExchanges]);

  return (
    <Card>
      <Box sx={{ bgcolor: theme.palette.background.paper }}>
        <Grid container sx={{ p: 1 }}>
          <Grid
            item
            xs={6}
            sm={3}
            sx={{ display: 'flex', alignItems: 'center' }}
          >
            {coinData.isStarred ? <StarIcon /> : <StarOutlineIcon />}
            <Typography sx={{ fontWeight: 700, ml: 2 }}>{title}</Typography>
          </Grid>
          <Grid
            item
            xs={3}
            sm={6}
            sx={{ display: 'flex', justifyContent: 'center' }}
          >
            <PeriodIntervalSelector
              defaultValue={selectedInterval}
              onChange={(value) => setSelectedInterval(value)}
            />
          </Grid>
          <Grid
            item
            xs={3}
            sm={3}
            sx={{ display: 'flex', justifyContent: 'end' }}
          >
            <KLineDataSelector
              defaultValue={selectedKLineData}
              onChange={(value) => setSelectedKLineData(value)}
            />
          </Grid>
        </Grid>
        <Box ref={chartContainerRef} sx={{ pt: 2 }} />
      </Box>
    </Card>
  );
}

export default React.memo(LightWeightKLineChart);
