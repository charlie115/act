import React, {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useState,
  useMemo,
  useRef,
} from 'react';

import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

import { LineType } from 'lightweight-charts';

import { DateTime } from 'luxon';

import { useSelector } from 'react-redux';

import orderBy from 'lodash/orderBy';
import uniqBy from 'lodash/uniqBy';

import { usePrevious } from '@uidotdev/usehooks';

import { useTranslation } from 'react-i18next';

import { useGetHistoricalKlineQuery } from 'redux/api/drf/infocore';
import { useGetRealTimeKlineQuery } from 'redux/api/websocket/kline';

import formatIntlNumber from 'utils/formatIntlNumber';
import formatShortNumber from 'utils/formatShortNumber';

import { DATE_FORMAT_API_QUERY } from 'constants';
import { INTERVAL_LIST } from 'constants/lists';

import LightWeightBaseChart from './LightWeightBaseChart';

const LightWeightPremiumKlineChart = forwardRef(
  (
    {
      baseAsset,
      dataType,
      interval,
      marketCodes,
      queryKey,
      isKimpExchange,
      isTetherPriceView,
    },
    ref
  ) => {
    const { loggedin, user } = useSelector((state) => state.auth);
    const { timezone } = useSelector((state) => state.app);
    const isAuthorized = loggedin && user.role !== 'visitor';

    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('md'));

    const { i18n, t } = useTranslation();

    const chartRef = useRef();

    const candlestickSeriesRef = useRef();
    const lineSeriesRef = useRef();

    const refetchTimeoutRef = useRef();

    const [startTime, setStartTime] = useState(null);
    const [endTime, setEndTime] = useState(null);

    const [currentData, setCurrentData] = useState([]);
    const [loadedHistoricalData, setLoadedHistoricalData] = useState([]);
    const [preloadedData, setPreloadedData] = useState([]);

    const reinitialize = () => {
      setStartTime(null);
      setEndTime(null);

      setCurrentData([]);
      setLoadedHistoricalData([]);
      setPreloadedData([]);

      candlestickSeriesRef.current?.setData([]);
      lineSeriesRef.current?.setData([]);
    };

    useImperativeHandle(
      ref,
      () => ({
        reinitialize,
      }),
      []
    );

    const { data } = useGetRealTimeKlineQuery(
      {
        ...marketCodes,
        interval,
        queryKey,
        component: 'kline-chart',
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
        interval,
        tz: timezone,
      },
      { skip: !marketCodes }
    );
    const {
      currentData: historicalData,
      isFetching: isFetchingHistoricalData,
      isSuccess: isSuccessHistoricalData,
    } = useGetHistoricalKlineQuery(
      {
        ...marketCodes,
        baseAsset,
        startTime,
        endTime,
        interval,
        tz: timezone,
      },
      {
        skip: !isAuthorized || !marketCodes || !(startTime && endTime),
      }
    );

    const chartRealTimeData = useMemo(() => {
      const value = data?.[baseAsset];
      if (!value || !dataType) return null;

      const time = value.datetime_now;

      const open = value[`${dataType}_open`] || 0;
      const high = value[`${dataType}_high`] || 0;
      const low = value[`${dataType}_low`] || 0;
      const close = value[`${dataType}_close`] || 0;

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
    }, [data?.[baseAsset], isTetherPriceView, dataType]);

    const chartHistoricalData = useMemo(() => {
      const candlestick = [];
      const line = [];
      if (!dataType) return { candlestick, line };

      currentData?.forEach((item) => {
        const time = DateTime.fromISO(item.datetime_now).toMillis();
        const open = item[`${dataType}_open`] || 0;
        const high = item[`${dataType}_high`] || 0;
        const low = item[`${dataType}_low`] || 0;
        const close = item[`${dataType}_close`] || 0;
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
    }, [currentData, isTetherPriceView, dataType]);

    // const { targetMarketCode, originMarketCode } = useMemo(
    //   () => ({
    //     targetMarketCode: MARKET_CODE_LIST.find(
    //       (o) => o.value === marketCodes?.targetMarketCode
    //     ),
    //     originMarketCode: MARKET_CODE_LIST.find(
    //       (o) => o.value === marketCodes?.originMarketCode
    //     ),
    //   }),
    //   [marketCodes]
    // );

    const intervalValue = useMemo(
      () => INTERVAL_LIST.find((o) => o.value === interval),
      [interval]
    );

    useEffect(
      () => () => {
        clearTimeout(refetchTimeoutRef.current);
      },
      [marketCodes, interval, isAuthorized]
    );

    useEffect(() => {
      setLoadedHistoricalData((state) => [...(historicalData || []), ...state]);
      if (isSuccessHistoricalData && historicalData?.length === 0) {
        // chartRef.current.timeScale().fitContent();
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
    }, [interval]);

    const prevQueryKey = usePrevious(queryKey);
    useEffect(() => {
      if (isAuthorized)
        if (prevQueryKey !== null)
          if (prevQueryKey !== queryKey) refetchInitialData();
    }, [queryKey, isAuthorized]);

    useEffect(() => {
      candlestickSeriesRef.current.setData(chartHistoricalData.candlestick);
      lineSeriesRef.current.setData(chartHistoricalData.line);
    }, [chartHistoricalData]);

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
    }, [interval, dataType, marketCodes]);

    useEffect(() => {
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

    return (
      <LightWeightBaseChart
        ref={chartRef}
        baseSeriesRef={candlestickSeriesRef}
        chartOptions={{
          leftPriceScale: { visible: true },
          rightPriceScale: { visible: true },
          handleScale: isAuthorized,
          handleScroll: isAuthorized,
        }}
        dependencies={[marketCodes, interval, dataType]}
        interval={intervalValue}
        isLoading={
          isLoadingInitialData ||
          (isFetchingInitialData && preloadedData.length === 0) ||
          isFetchingHistoricalData
        }
        isUnauthorized={!isAuthorized}
        onBarsInfoChanged={({ start, end }) => {
          if (!isFetchingHistoricalData) {
            setEndTime(end.toFormat(DATE_FORMAT_API_QUERY));
            setStartTime(
              start.startOf('minute').toFormat(DATE_FORMAT_API_QUERY)
            );
          }
        }}
        onReady={(baseChartRef) => {
          candlestickSeriesRef.current =
            baseChartRef.current.addCandlestickSeries({
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
            });
          lineSeriesRef.current = baseChartRef.current.addLineSeries({
            priceScaleId: 'left',
            color: theme.palette.primary.main,
            crosshairMarkerVisible: false,
            lineType: LineType.Curved,
            lineWidth: 1,
            priceFormat: {
              minMove: 0.001,
              type: 'custom',
              formatter: (price) => formatIntlNumber(price, 2, 1),
            },
            title: t('Price'),
          });
        }}
      />
    );
  }
);

export default LightWeightPremiumKlineChart;
