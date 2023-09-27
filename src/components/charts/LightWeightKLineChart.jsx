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
import LinearProgress from '@mui/material/LinearProgress';
import Paper from '@mui/material/Paper';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import StarIcon from '@mui/icons-material/Star';
import StarOutlineIcon from '@mui/icons-material/StarOutline';

import {
  createChart,
  ColorType,
  CrosshairMode,
  LineType,
} from 'lightweight-charts';

import { DateTime } from 'luxon';

import debounce from 'lodash/debounce';
import isUndefined from 'lodash/isUndefined';
import sortBy from 'lodash/sortBy';

import { usePrevious } from '@uidotdev/usehooks';

import { useTranslation } from 'react-i18next';
import { alpha, useTheme } from '@mui/material/styles';

import { useGetHistoricalKlineQuery } from 'redux/api/drfKline';
import { useGetRealTimeKlineQuery } from 'redux/api/websocket';

import IntervalSelector from 'components/IntervalSelector';
import KlineDataSelector from 'components/KlineDataSelector';

import { DATE_FORMAT_API_QUERY } from 'constants';
import { INTERVAL_LIST } from 'constants/lists';

// const KLINE_DATA_KEY = 'tp';
// const REALTIME_INTERVAL_KEY = '1T,1,minutes';

function LightWeightKlineChart({
  baseAsset,
  marketCodes,
  onAddFavoriteAsset,
  onRemoveFavoriteAsset,
}) {
  const theme = useTheme();
  const { i18n, t } = useTranslation();

  const chartRef = useRef();
  const chartContainerRef = useRef();

  const candlestickSeriesRef = useRef();
  const lineSeriesRef = useRef();

  const refetchTimeoutRef = useRef();

  const [title, setTitle] = useState();

  const [interval, setInterval] = useState('1T');

  const [klineDataType, setKlineDataType] = useState('tp');

  const [startTime, setStartTime] = useState(null);
  const [endTime, setEndTime] = useState(null);

  const {
    data: initialData,
    refetch: refetchInitialData,
    isFetching: isFetchingInitialData,
    isLoading: isLoadingInitialData,
    isUninitialized: isUninitializedInitialData,
  } = useGetHistoricalKlineQuery(
    {
      ...marketCodes,
      interval,
      baseAsset: baseAsset?.name,
    },
    { skip: !marketCodes }
  );
  const { data: historicalData } = useGetHistoricalKlineQuery(
    {
      ...marketCodes,
      interval,
      baseAsset: baseAsset?.name,
      startTime,
      endTime,
    },
    { skip: !marketCodes || !(startTime && endTime) }
  );

  const { data } = useGetRealTimeKlineQuery(
    { ...marketCodes, interval },
    { skip: !marketCodes }
  );

  const chartRealTimeData = useMemo(() => {
    const value = data?.[baseAsset.name];
    if (!value) return null;

    const time = DateTime.fromMillis(value.datetime_now)
      .setZone('local')
      .toMillis();
    return {
      candlestick: {
        time,
        open: value[`${klineDataType}_open`],
        high: value[`${klineDataType}_high`],
        low: value[`${klineDataType}_low`],
        close: value[`${klineDataType}_close`],
      },
      line: { time, value: value.tp },
    };
  }, [data?.[baseAsset.name], klineDataType]);

  const chartHistoricalData = useMemo(() => {
    const candlestick = [];
    const line = [];
    sortBy(
      [...(historicalData || []), ...(initialData || [])],
      'datetime_now'
    )?.forEach((item) => {
      const time = DateTime.fromISO(item.datetime_now).toMillis();
      candlestick.push({
        time,
        open: item[`${klineDataType}_open`],
        high: item[`${klineDataType}_high`],
        low: item[`${klineDataType}_low`],
        close: item[`${klineDataType}_close`],
      });
      line.push({
        time,
        value: item.tp,
      });
    });
    return { candlestick, line };
  }, [historicalData, initialData, klineDataType]);

  const onVisibleLogicalRangeChange = (newVisibleLogicalRange) => {
    const barsInfo = candlestickSeriesRef.current.barsInLogicalRange(
      newVisibleLogicalRange
    );
    if (barsInfo !== null && barsInfo.barsBefore < 0) {
      console.log('barsInfo: ', barsInfo);
      const { quantity, unit } = INTERVAL_LIST.find(
        (o) => o.value === interval
      );
      const latestInitial = initialData?.slice(-1);
      let newEndTime = DateTime.now();
      if (latestInitial?.datetime_now)
        newEndTime = DateTime.fromISO(latestInitial?.datetime_now).minus({
          [unit]: 1,
        });
      const newStartTime = newEndTime.minus({
        [unit]: quantity * Math.abs(Math.round(barsInfo.barsBefore)),
      });
      setStartTime(
        newStartTime.startOf('minute').toFormat(DATE_FORMAT_API_QUERY)
      );
      setEndTime(newEndTime.startOf('minute').toFormat(DATE_FORMAT_API_QUERY));
    }
  };
  const debouncedOnVisibleLogicalRangeChange = useCallback(
    debounce(onVisibleLogicalRangeChange, 1000, {
      leading: false,
      trailing: true,
    }),
    [initialData, interval]
  );

  const onVisibleTimeRangeChange = useCallback((newTimeRange) => {
    // console.log('newTimeRange: ', newTimeRange);
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
      rightOffset: 2,
      tickMarkFormatter: (time) => DateTime.fromMillis(time).toFormat('HH:mm'),
    });
    chartRef.current
      .timeScale()
      .subscribeVisibleLogicalRangeChange(debouncedOnVisibleLogicalRangeChange);
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
      // title: t('Premium'),
    });
    lineSeriesRef.current = chartRef.current.addLineSeries({
      priceScaleId: 'left',
      color: theme.palette.primary.main,
      crosshairMarkerVisible: false,
      // lastValueVisible: false,
      lineType: LineType.Curved,
      lineWidth: 1,
      priceFormat: { minMove: 0.01, precision: 2, type: 'price' },
      title: t('Price'),
    });

    return () => {
      chartRef.current
        .timeScale()
        .unsubscribeVisibleLogicalRangeChange(onVisibleLogicalRangeChange);
      chartRef.current
        .timeScale()
        .unsubscribeVisibleTimeRangeChange(onVisibleTimeRangeChange);
      clearTimeout(refetchTimeoutRef.current);
    };
  }, []);

  useEffect(() => {
    // set
  }, [historicalData]);

  useEffect(() => {
    candlestickSeriesRef.current.setData(chartHistoricalData.candlestick);
    lineSeriesRef.current.setData(chartHistoricalData.line);
    // chartRef.current.timeScale().fitContent();
  }, [chartHistoricalData]);

  useEffect(() => {
    if (!isFetchingInitialData && chartRealTimeData) {
      candlestickSeriesRef.current.update(chartRealTimeData.candlestick);
      lineSeriesRef.current.update(chartRealTimeData.line);
    }
  }, [chartRealTimeData, isFetchingInitialData]);

  const prevTimestamp = usePrevious(data?.[baseAsset.name]?.datetime_now);
  useEffect(() => {
    if (
      !isUninitializedInitialData &&
      prevTimestamp &&
      prevTimestamp !== data?.[baseAsset.name]?.datetime_now
    )
      refetchTimeoutRef.current = setTimeout(() => {
        try {
          refetchInitialData();
        } catch {
          /* no-op */
        }
      }, 5000);
  }, [isUninitializedInitialData, data?.[baseAsset.name]?.datetime_now]);

  useEffect(() => {
    if (refetchTimeoutRef.current) clearTimeout(refetchTimeoutRef.current);
  }, [interval, klineDataType, marketCodes]);

  useEffect(() => {
    // candlestickSeriesRef?.current.applyOptions({
    //   title: `${
    //     marketCodes?.targetMarketCode.includes('UPBIT')
    //       ? t('KIMP')
    //       : t('Premium')
    //   } (${klineDataType.toUpperCase()})`,
    // });
    // chartRef.current.timeScale().applyOptions({
    //   rightOffset: marketCodes?.targetMarketCode.includes('UPBIT') ? 10 : 15,
    // });
  }, [i18n.language, marketCodes, klineDataType]);

  useEffect(() => {
    const value = marketCodes?.targetMarketCode;
    setTitle(`${baseAsset.name} / ${value?.split('/').pop()}`);
  }, [marketCodes]);

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

  const isFavorite = !isUndefined(baseAsset.favoriteAssetId);

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
            <Tooltip
              title={
                isFavorite ? t('Remove from favorites') : t('Add to favorites')
              }
            >
              <StarIcon
                color={isFavorite ? 'accent' : 'secondary'}
                onClick={() =>
                  isFavorite
                    ? onRemoveFavoriteAsset(baseAsset.favoriteAssetId)
                    : onAddFavoriteAsset(baseAsset.name)
                }
                sx={{
                  '& :hover': {
                    color: theme.palette.accent.main,
                    opacity: 0.5,
                  },
                }}
              />
            </Tooltip>
            <Typography sx={{ fontWeight: 700, ml: 2 }}>{title}</Typography>
          </Grid>
          <Grid
            item
            xs={3}
            sm={6}
            sx={{ display: 'flex', justifyContent: 'center' }}
          >
            <IntervalSelector
              defaultValue={interval}
              onChange={(value) => {
                setInterval(value);
                // setStartTime(DateTime.now());
              }}
            />
          </Grid>
          <Grid
            item
            xs={3}
            sm={3}
            sx={{ display: 'flex', justifyContent: 'end' }}
          >
            <KlineDataSelector
              defaultValue={klineDataType}
              onChange={(value) => setKlineDataType(value)}
            />
          </Grid>
        </Grid>
        <Box ref={chartContainerRef} sx={{ pt: 2 }}>
          {isLoadingInitialData && <LinearProgress />}
        </Box>
      </Box>
    </Card>
  );
}

export default React.memo(LightWeightKlineChart);
