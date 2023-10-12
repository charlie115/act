import React, {
  useCallback,
  useEffect,
  useState,
  useMemo,
  useRef,
} from 'react';

import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Grid from '@mui/material/Grid';
import LinearProgress from '@mui/material/LinearProgress';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import StarIcon from '@mui/icons-material/Star';

import { createChart, CrosshairMode, LineType } from 'lightweight-charts';

import { DateTime } from 'luxon';

import debounce from 'lodash/debounce';
import isUndefined from 'lodash/isUndefined';
import uniqBy from 'lodash/uniqBy';

import { usePrevious } from '@uidotdev/usehooks';

import { useTranslation } from 'react-i18next';
import { alpha, useTheme } from '@mui/material/styles';

import { useGetHistoricalKlineQuery } from 'redux/api/drf/kline';
import { useGetRealTimeKlineQuery } from 'redux/api/websocket/kline';

import formatIntlNumber from 'utils/formatIntlNumber';

import IntervalSelector from 'components/IntervalSelector';
import KlineDataSelector from 'components/KlineDataSelector';

import { DATE_FORMAT_API_QUERY } from 'constants';
import { INTERVAL_LIST } from 'constants/lists';

const CHART_HEIGHT = 300;

function LightWeightKlineChart({
  baseAsset,
  marketCodes,
  isKimpExchange,
  isTetherPriceView,
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

  const [barsInfo, setBarsInfo] = useState(null);

  const [startTime, setStartTime] = useState(null);
  const [endTime, setEndTime] = useState(null);

  const [currentData, setCurrentData] = useState([]);

  const { data } = useGetRealTimeKlineQuery(
    { ...marketCodes, interval },
    { skip: !marketCodes }
  );

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
  const { data: historicalData, isFetching: isFetchingHistoricalData } =
    useGetHistoricalKlineQuery(
      {
        ...marketCodes,
        interval,
        baseAsset: baseAsset?.name,
        startTime,
        endTime,
      },
      {
        skip: !marketCodes || !(startTime && endTime),
      }
    );

  const chartRealTimeData = useMemo(() => {
    const value = data?.[baseAsset.name];
    if (!value) return null;

    const time = value.datetime_now;

    if (isKimpExchange && isTetherPriceView)
      return {
        candlestick: {
          time,
          open: value.dollar * (1 + value[`${klineDataType}_open`] * 0.01),
          high: value.dollar * (1 + value[`${klineDataType}_high`] * 0.01),
          low: value.dollar * (1 + value[`${klineDataType}_low`] * 0.01),
          close: value.dollar * (1 + value[`${klineDataType}_close`] * 0.01),
        },
        line: { time, value: value.tp },
      };
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
  }, [data?.[baseAsset.name], isTetherPriceView, klineDataType]);

  const chartHistoricalData = useMemo(() => {
    const candlestick = [];
    const line = [];
    [...currentData, ...(initialData || [])].forEach((item) => {
      const time = DateTime.fromISO(item.datetime_now).toMillis();
      if (isKimpExchange && isTetherPriceView)
        candlestick.push({
          time,
          open: item.dollar * (1 + item[`${klineDataType}_open`] * 0.01),
          high: item.dollar * (1 + item[`${klineDataType}_high`] * 0.01),
          low: item.dollar * (1 + item[`${klineDataType}_low`] * 0.01),
          close: item.dollar * (1 + item[`${klineDataType}_close`] * 0.01),
        });
      else
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
  }, [currentData, initialData, isTetherPriceView, klineDataType]);

  const onVisibleLogicalRangeChange = (newVisibleLogicalRange) => {
    const newBarsInfo = candlestickSeriesRef.current.barsInLogicalRange(
      newVisibleLogicalRange
    );
    if (newBarsInfo !== null && Math.floor(newBarsInfo.barsBefore) < 0)
      setBarsInfo(newBarsInfo);
  };
  const debouncedOnVisibleLogicalRangeChange = useCallback(
    debounce(onVisibleLogicalRangeChange, 500, {
      leading: false,
      trailing: true,
    }),
    [endTime, interval]
  );

  const reinitialize = () => {
    setBarsInfo(null);
    setStartTime(null);
    setEndTime(null);

    setCurrentData([]);

    candlestickSeriesRef.current?.setData([]);
    lineSeriesRef.current?.setData([]);
  };

  useEffect(() => {
    if (chartRef.current) chartRef.current.remove();
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
      height: CHART_HEIGHT,
    });
    chartRef.current.priceScale('left').applyOptions({
      borderColor: alpha(theme.palette.secondary.main, 0.2),
    });
    chartRef.current.priceScale('right').applyOptions({
      borderColor: alpha(theme.palette.secondary.main, 0.2),
      // mode: PriceScaleMode.Logarithmic,
    });
    chartRef.current.timeScale().applyOptions({
      barSpacing: 10,
      borderColor: alpha(theme.palette.secondary.main, 0.2),
      fixRightEdge: true,
      rightOffset: 2,
      tickMarkFormatter: (time) => DateTime.fromMillis(time).toFormat('HH:mm'),
    });
    chartRef.current
      .timeScale()
      .subscribeVisibleLogicalRangeChange(debouncedOnVisibleLogicalRangeChange);

    candlestickSeriesRef.current = chartRef.current.addCandlestickSeries({
      priceScaleId: 'right',
      downColor: theme.palette.error.main,
      upColor: theme.palette.success.main,
      wickDownColor: theme.palette.error.main,
      wickUpColor: theme.palette.success.main,
      priceFormat: {
        minMove: 0.001,
        type: 'custom',
        formatter: (price) =>
          `${formatIntlNumber(price, 1, isTetherPriceView ? 1 : 3)} ${
            isTetherPriceView ? t('KRW') : '%'
          }`,
      },
      // priceFormat: { minMove: 0.00001, precision: 5, type: 'percent' },
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
        .unsubscribeVisibleLogicalRangeChange(
          debouncedOnVisibleLogicalRangeChange
        );
      clearTimeout(refetchTimeoutRef.current);
    };
  }, [marketCodes, interval, isTetherPriceView, i18n.language]);

  useEffect(() => {
    setCurrentData((state) =>
      uniqBy([...(historicalData || []), ...state], 'datetime_now')
    );
    if (historicalData?.length === 0) {
      chartRef.current.timeScale().fitContent();
      setBarsInfo(null);
    }
  }, [historicalData]);

  useEffect(() => {
    chartRef.current.timeScale().scrollToRealTime();
  }, [interval]);

  useEffect(() => {
    if (!isFetchingHistoricalData && barsInfo) {
      const { quantity, unit } = INTERVAL_LIST.find(
        (o) => o.value === interval
      );
      const newEndTime = DateTime.fromMillis(barsInfo.from).minus({
        [unit]: 1,
      });
      const newStartTime = newEndTime.minus({
        [unit]: quantity * Math.abs(Math.floor(barsInfo.barsBefore)) * 50,
      });
      setEndTime(newEndTime.toFormat(DATE_FORMAT_API_QUERY));
      setStartTime(
        newStartTime.startOf('minute').toFormat(DATE_FORMAT_API_QUERY)
      );
    }
  }, [barsInfo, interval, isFetchingHistoricalData]);

  useEffect(() => {
    candlestickSeriesRef.current.setData(chartHistoricalData.candlestick);
    lineSeriesRef.current.setData(chartHistoricalData.line);
  }, [chartHistoricalData, barsInfo]);

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
    reinitialize();
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
    <Card onClick={(e) => e.stopPropagation()}>
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
                onClick={(e) => {
                  e.stopPropagation();
                  if (isFavorite)
                    onRemoveFavoriteAsset(baseAsset.favoriteAssetId);
                  else onAddFavoriteAsset(baseAsset.name);
                }}
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
                reinitialize();
                setInterval(value);
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
              isKimpExchange={isKimpExchange}
              isTetherPriceView={isTetherPriceView}
              onChange={(value) => setKlineDataType(value)}
            />
          </Grid>
        </Grid>
        {(isLoadingInitialData || isFetchingHistoricalData) && (
          <LinearProgress />
        )}
        <Box
          ref={chartContainerRef}
          sx={{ pt: 2 }}
          onClick={(e) => e.stopPropagation()}
        />
      </Box>
    </Card>
  );
}

export default React.memo(LightWeightKlineChart);
