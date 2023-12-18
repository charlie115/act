import React, {
  useCallback,
  useEffect,
  useState,
  useMemo,
  useRef,
} from 'react';

import { useNavigate } from 'react-router-dom';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import Grid from '@mui/material/Grid';
import IconButton from '@mui/material/IconButton';
import LinearProgress from '@mui/material/LinearProgress';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import ArrowForwardIosIcon from '@mui/icons-material/ArrowForwardIos';
import ArrowRightAltIcon from '@mui/icons-material/ArrowRightAlt';
import StarIcon from '@mui/icons-material/Star';

import { alpha, useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

import { createChart, CrosshairMode, LineType } from 'lightweight-charts';

import { DateTime } from 'luxon';

import { useSelector } from 'react-redux';

import debounce from 'lodash/debounce';
import isNaN from 'lodash/isNaN';
import isUndefined from 'lodash/isUndefined';
import orderBy from 'lodash/orderBy';
import uniqBy from 'lodash/uniqBy';

import { usePrevious } from '@uidotdev/usehooks';

import { useTranslation } from 'react-i18next';

import { useGetHistoricalKlineQuery } from 'redux/api/drf/infocore';
import { useGetRealTimeKlineQuery } from 'redux/api/websocket/kline';

import formatIntlNumber from 'utils/formatIntlNumber';
import formatShortNumber from 'utils/formatShortNumber';

import ExchangeWalletNetworks from 'components/ExchangeWalletNetworks';
import IntervalSelector from 'components/IntervalSelector';
import KlineDataSelector from 'components/KlineDataSelector';

import { DATE_FORMAT_API_QUERY } from 'constants';
import { INTERVAL_LIST, MARKET_CODE_LIST } from 'constants/lists';

const CHART_HEIGHT = 250;

function LightWeightKlineChart({
  baseAssetData,
  marketCodes,
  isKimpExchange,
  isTetherPriceView,
  onAddFavoriteAsset,
  onRemoveFavoriteAsset,
  queryKey,
  showMarketCodes,
}) {
  const navigate = useNavigate();

  const {
    name: baseAsset,
    favoriteAssetId,
    walletNetworks,
    walletStatus,
  } = baseAssetData;

  const { loggedin, user } = useSelector((state) => state.auth);
  const { timezone } = useSelector((state) => state.app);
  const isAuthorized = loggedin && user.role !== 'visitor';

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const { i18n, t } = useTranslation();

  const chartRef = useRef();
  const chartContainerRef = useRef();
  const wrapperRef = useRef();

  const candlestickSeriesRef = useRef();
  const lineSeriesRef = useRef();

  const refetchTimeoutRef = useRef();

  const [title, setTitle] = useState();

  const [klineInterval, setKlineInterval] = useState('1T');

  const [klineDataType, setKlineDataType] = useState();
  const [disabledKlineDataType, setDisabledKlineDataType] = useState();

  const [barsInfo, setBarsInfo] = useState(null);

  const [startTime, setStartTime] = useState(null);
  const [endTime, setEndTime] = useState(null);

  const [currentData, setCurrentData] = useState([]);
  const [loadedHistoricalData, setLoadedHistoricalData] = useState([]);
  const [preloadedData, setPreloadedData] = useState([]);

  const { data } = useGetRealTimeKlineQuery(
    {
      ...marketCodes,
      interval: klineInterval,
      component: 'kline-chart',
      queryKey,
    },
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
      baseAsset,
      interval: klineInterval,
      tz: timezone,
    },
    { skip: !marketCodes }
  );
  const {
    data: historicalData,
    isFetching: isFetchingHistoricalData,
    isSuccess: isSuccessHistoricalData,
  } = useGetHistoricalKlineQuery(
    {
      ...marketCodes,
      baseAsset,
      startTime,
      endTime,
      interval: klineInterval,
      tz: timezone,
    },
    {
      skip:
        !isAuthorized ||
        !marketCodes ||
        !(startTime && endTime) ||
        barsInfo?.barsBefore > 0,
    }
  );

  const chartRealTimeData = useMemo(() => {
    const value = data?.[baseAsset];
    if (!value || !klineDataType) return null;

    const time = value.datetime_now;

    const open = value[`${klineDataType}_open`] || 0;
    const high = value[`${klineDataType}_high`] || 0;
    const low = value[`${klineDataType}_low`] || 0;
    const close = value[`${klineDataType}_close`] || 0;

    if (isKimpExchange && isTetherPriceView)
      return {
        candlestick: {
          time,
          open: value.dollar * (1 + open * 0.01),
          high: value.dollar * (1 + high * 0.01),
          low: value.dollar * (1 + low * 0.01),
          close: value.dollar * (1 + close * 0.01),
        },
        line: value.tp !== null ? { time, value: value.tp } : undefined,
      };
    return {
      candlestick: { time, open, high, low, close },
      line: value.tp !== null ? { time, value: value.tp } : undefined,
    };
  }, [data?.[baseAsset], isTetherPriceView, klineDataType]);

  const chartHistoricalData = useMemo(() => {
    const candlestick = [];
    const line = [];
    if (!klineDataType) return { candlestick, line };

    currentData?.forEach((item) => {
      const time = DateTime.fromISO(item.datetime_now).toMillis();
      const open = item[`${klineDataType}_open`] || 0;
      const high = item[`${klineDataType}_high`] || 0;
      const low = item[`${klineDataType}_low`] || 0;
      const close = item[`${klineDataType}_close`] || 0;
      if (isKimpExchange && isTetherPriceView)
        candlestick.push({
          time,
          open: item.dollar * (1 + open * 0.01),
          high: item.dollar * (1 + high * 0.01),
          low: item.dollar * (1 + low * 0.01),
          close: item.dollar * (1 + close * 0.01),
        });
      else candlestick.push({ time, open, high, low, close });
      if (item.tp !== null)
        line.push({
          time,
          value: item.tp,
        });
    });
    return { candlestick, line };
  }, [currentData, isTetherPriceView, klineDataType]);

  const { targetMarketCode, originMarketCode } = useMemo(
    () => ({
      targetMarketCode: MARKET_CODE_LIST.find(
        (o) => o.value === marketCodes?.targetMarketCode
      ),
      originMarketCode: MARKET_CODE_LIST.find(
        (o) => o.value === marketCodes?.originMarketCode
      ),
    }),
    [marketCodes]
  );

  const onVisibleLogicalRangeChange = (newVisibleLogicalRange) => {
    const newBarsInfo = candlestickSeriesRef.current.barsInLogicalRange(
      newVisibleLogicalRange
    );
    if (newBarsInfo && Math.floor(newBarsInfo.barsAfter) === 0)
      setBarsInfo(null);
    else setBarsInfo(newBarsInfo);
  };
  const debouncedOnVisibleLogicalRangeChange = useCallback(
    debounce(onVisibleLogicalRangeChange, 500, {
      leading: false,
      trailing: true,
    }),
    []
  );

  const reinitialize = () => {
    setBarsInfo(null);
    setStartTime(null);
    setEndTime(null);

    setCurrentData([]);
    setLoadedHistoricalData([]);
    setPreloadedData([]);

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
        horzLines: { color: alpha(theme.palette.grey['600'], 0.15) },
        vertLines: { color: alpha(theme.palette.grey['600'], 0.15) },
      },
      handleScale: isAuthorized,
      handleScroll: isAuthorized,
      localization: {
        timeFormatter: (time) =>
          DateTime.fromMillis(time).toFormat('DD HH:mm:ss'),
      },
      crosshair: { mode: CrosshairMode.Normal },
      width: chartContainerRef.current?.clientWidth,
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
          `${formatIntlNumber(price, 2, 2)} ${
            isTetherPriceView ? t('KRW') : '%'
          }`,
      },
      // priceFormat: { minMove: 0.00001 precision: 5, type: 'percent' },
      // title: t('Premium'),
    });
    lineSeriesRef.current = chartRef.current.addLineSeries({
      priceScaleId: 'left',
      color: theme.palette.primary.main,
      crosshairMarkerVisible: false,
      // lastValueVisible: false,
      // lastPriceAnimation: LastPriceAnimationMode.OnDataUpdate,
      lineType: LineType.Curved,
      lineWidth: 1,
      priceFormat: {
        minMove: 0.001,
        type: 'custom',
        formatter: (price) => formatIntlNumber(price, 2, 1),
      },
      title: t('Price'),
    });

    if (!isAuthorized) {
      // chartRef.current.timeScale().fitContent();
      const canvas = document.querySelector(
        '.tv-lightweight-charts td:nth-child(2) canvas:nth-child(2)'
      );
      canvas.style.backdropFilter = 'blur(10px)';
      canvas.style['-webkit-backdrop-filter'] = 'blur(10px)';
      canvas.style.pointerEvents = 'none';
    }

    return () => {
      chartRef.current
        .timeScale()
        .unsubscribeVisibleLogicalRangeChange(
          debouncedOnVisibleLogicalRangeChange
        );
      clearTimeout(refetchTimeoutRef.current);
    };
  }, [marketCodes, klineInterval, isAuthorized]);

  useEffect(() => {
    if (!klineDataType) {
      if (data?.[baseAsset]) {
        const { tp } = data[baseAsset];
        if (tp && !isNaN(tp)) setKlineDataType('tp');
        else {
          setKlineDataType('LS');
          setDisabledKlineDataType({ tp: true });
        }
      }
    }
  }, [data?.[baseAsset], klineDataType]);

  useEffect(() => {
    setLoadedHistoricalData((state) => [...(historicalData || []), ...state]);
    if (isSuccessHistoricalData && historicalData?.length === 0) {
      chartRef.current.timeScale().fitContent();
      setBarsInfo(null);
      setStartTime(null);
      setEndTime(null);
    }
  }, [historicalData, isSuccessHistoricalData]);

  useEffect(() => {
    setPreloadedData(initialData || []);
  }, [initialData]);

  useEffect(() => {
    setCurrentData(
      orderBy(
        uniqBy([...loadedHistoricalData, ...preloadedData], 'datetime_now'),
        (o) => DateTime.fromISO(o.datetime_now).toMillis(),
        'asc'
      )
    );
  }, [loadedHistoricalData, preloadedData]);

  useEffect(() => {
    chartRef.current.timeScale().scrollToRealTime();
  }, [klineInterval]);

  const prevQueryKey = usePrevious(queryKey);
  useEffect(() => {
    if (isAuthorized)
      if (prevQueryKey !== null)
        if (prevQueryKey !== queryKey) refetchInitialData();
  }, [queryKey, isAuthorized]);

  const prevBarsInfo = usePrevious(barsInfo);
  useEffect(() => {
    if (
      !isFetchingHistoricalData &&
      barsInfo &&
      Math.floor(barsInfo.barsBefore) < 0
    ) {
      const diff = prevBarsInfo
        ? Math.floor(prevBarsInfo.barsBefore) - Math.floor(barsInfo.barsBefore)
        : 0;
      if (!prevBarsInfo || Math.abs(diff) > 10) {
        const { quantity, unit } = INTERVAL_LIST.find(
          (o) => o.value === klineInterval
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
    }
  }, [barsInfo, klineInterval, isFetchingHistoricalData]);

  useEffect(() => {
    candlestickSeriesRef.current.setData(chartHistoricalData.candlestick);
    lineSeriesRef.current.setData(chartHistoricalData.line);
  }, [chartHistoricalData, barsInfo]);

  useEffect(() => {
    if (
      !isFetchingInitialData &&
      !isFetchingHistoricalData &&
      chartRealTimeData
    ) {
      if (chartRealTimeData.candlestick)
        candlestickSeriesRef.current.update(chartRealTimeData.candlestick);
      if (chartRealTimeData.line)
        lineSeriesRef.current.update(chartRealTimeData.line);
    }
  }, [chartRealTimeData, isFetchingHistoricalData, isFetchingInitialData]);

  const prevTimestamp = usePrevious(data?.[baseAsset]?.datetime_now);
  useEffect(() => {
    if (
      isAuthorized &&
      !isUninitializedInitialData &&
      prevTimestamp &&
      prevTimestamp !== data?.[baseAsset]?.datetime_now
    )
      refetchTimeoutRef.current = setTimeout(() => {
        try {
          refetchInitialData();
        } catch {
          /* no-op */
        }
      }, 5000);
  }, [
    isAuthorized,
    isUninitializedInitialData,
    data?.[baseAsset]?.datetime_now,
  ]);

  useEffect(() => {
    if (refetchTimeoutRef.current) clearTimeout(refetchTimeoutRef.current);
  }, [klineInterval, klineDataType, marketCodes]);

  useEffect(() => {
    const value = marketCodes?.targetMarketCode;
    setTitle(`${baseAsset} / ${value?.split('/').pop()}`);
    if (marketCodes) setKlineInterval('1T');
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

  useEffect(() => {
    chartRef.current.applyOptions({
      layout: { fontSize: isMobile ? 8 : 11 },
    });
    candlestickSeriesRef.current.applyOptions({
      priceFormat: {
        minMove: 0.001,
        type: 'custom',
        formatter: (price) =>
          `${formatIntlNumber(price, 2, 2)} ${
            isTetherPriceView ? t('KRW') : '%'
          }`,
      },
    });
    lineSeriesRef.current.applyOptions({
      priceFormat: {
        minMove: 0.001,
        type: 'custom',
        formatter: (price) =>
          isMobile
            ? formatShortNumber(price, 2)
            : formatIntlNumber(price, 2, 1),
      },
      title: t('Price'),
    });
  }, [isMobile, isTetherPriceView, i18n.language]);

  const isFavorite = !isUndefined(favoriteAssetId);

  return (
    <Card
      ref={wrapperRef}
      onClick={(e) => e.stopPropagation()}
      sx={{ borderRadius: 0 }}
    >
      <Box sx={{ bgcolor: 'background.paper' }}>
        {(targetMarketCode?.value.includes('SPOT') ||
          originMarketCode?.value.includes('SPOT')) && (
          <Box sx={{ p: 2 }}>
            <ExchangeWalletNetworks
              direction={
                targetMarketCode.value.includes('SPOT') &&
                originMarketCode.value.includes('SPOT') &&
                targetMarketCode.exchange !== originMarketCode.exchange
                  ? 'right'
                  : 'all'
              }
              targetMarketCode={targetMarketCode}
              originMarketCode={originMarketCode}
              walletNetworks={walletNetworks}
              walletStatus={walletStatus}
            />
            {targetMarketCode.value.includes('SPOT') &&
              originMarketCode.value.includes('SPOT') &&
              targetMarketCode.exchange !== originMarketCode.exchange && (
                <ExchangeWalletNetworks
                  direction="left"
                  targetMarketCode={targetMarketCode}
                  originMarketCode={originMarketCode}
                  walletNetworks={walletNetworks}
                  walletStatus={walletStatus}
                />
              )}
          </Box>
        )}
        <Grid container sx={{ p: 1, pt: 2 }}>
          <Grid
            item
            xs={6}
            sm={3}
            sx={{ display: 'flex', alignItems: 'center' }}
          >
            {onAddFavoriteAsset && onRemoveFavoriteAsset && (
              <Tooltip
                title={
                  isFavorite
                    ? t('Remove from favorites')
                    : t('Add to favorites')
                }
              >
                <StarIcon
                  color={isFavorite ? 'accent' : 'secondary'}
                  onClick={(e) => {
                    e.stopPropagation();
                    if (isFavorite) onRemoveFavoriteAsset(favoriteAssetId);
                    else onAddFavoriteAsset(baseAsset);
                  }}
                  sx={{
                    '& :hover': {
                      color: theme.palette.accent.main,
                      opacity: 0.5,
                    },
                  }}
                />
              </Tooltip>
            )}
            <Typography sx={{ fontWeight: 700, ml: 2 }}>{title}</Typography>
          </Grid>
          <Grid
            item
            xs={3}
            sm={6}
            sx={{ display: 'flex', justifyContent: 'center' }}
          >
            <IntervalSelector
              defaultValue={klineInterval}
              disabled={
                isFetchingInitialData ||
                isFetchingHistoricalData ||
                !isAuthorized
              }
              onChange={(value) => {
                reinitialize();
                setKlineInterval(value);
              }}
            />
          </Grid>
          <Grid
            item
            xs={3}
            sm={3}
            sx={{ display: 'flex', justifyContent: 'end' }}
          >
            {klineDataType && (
              <KlineDataSelector
                defaultValue={klineDataType}
                disabled={disabledKlineDataType}
                isKimpExchange={isKimpExchange}
                isTetherPriceView={isTetherPriceView}
                onChange={(value) => setKlineDataType(value)}
              />
            )}
          </Grid>
        </Grid>
        {(isLoadingInitialData ||
          (isFetchingInitialData && preloadedData.length === 0) ||
          isFetchingHistoricalData) && <LinearProgress />}
        {showMarketCodes && (
          <Stack
            direction="row"
            alignItems="center"
            justifyContent="center"
            spacing={1}
            mt={2}
          >
            <Box
              component="img"
              src={targetMarketCode.icon}
              alt={targetMarketCode.getLabel()}
              sx={{ height: { xs: 16, md: 18 }, width: { xs: 16, md: 18 } }}
            />
            <Box>{targetMarketCode.getLabel()}</Box>
            <ArrowRightAltIcon />
            <Box
              component="img"
              src={originMarketCode.icon}
              alt={originMarketCode.getLabel()}
              sx={{ height: { xs: 16, md: 18 }, width: { xs: 16, md: 18 } }}
            />
            <Box>{originMarketCode.getLabel()}</Box>
          </Stack>
        )}
        <Box
          ref={chartContainerRef}
          sx={{ position: 'relative', pt: 2 }}
          onClick={(e) => e.stopPropagation()}
        >
          {!isLoadingInitialData && !isAuthorized && (
            <Button
              color="error"
              size="large"
              onClick={() => navigate('/login')}
              sx={{
                position: 'absolute',
                top: '35%',
                left: '50%',
                transform: 'translateX(-50%)',
                zIndex: 3,
              }}
            >
              {t('Login to view data')}
            </Button>
          )}
          {barsInfo?.barsAfter > 100 && (
            <IconButton
              color="dark"
              size="small"
              onClick={() => {
                chartRef.current.timeScale().scrollToPosition(0, true);
                setBarsInfo(null);
                setTimeout(
                  () =>
                    chartRef.current
                      .timeScale()
                      .applyOptions({ rightOffset: 2, fixRightEdge: true }),
                  0
                );
              }}
              sx={{
                bgcolor: 'accent.main',
                position: 'absolute',
                bottom: 10,
                right: 10,
                zIndex: 3,
                ':hover': { bgcolor: 'accent.main', opacity: 0.7 },
              }}
            >
              <ArrowForwardIosIcon />
            </IconButton>
          )}
        </Box>
      </Box>
    </Card>
  );
}

export default LightWeightKlineChart;
