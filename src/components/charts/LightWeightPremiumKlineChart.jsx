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

import isNumber from 'lodash/isNumber';
import orderBy from 'lodash/orderBy';
import uniqBy from 'lodash/uniqBy';

import { usePrevious } from '@uidotdev/usehooks';

import { useTranslation } from 'react-i18next';

import { useGetHistoricalKlineQuery } from 'redux/api/drf/infocore';
import { useGetRealTimeKlineQuery } from 'redux/api/websocket/kline';

import formatIntlNumber from 'utils/formatIntlNumber';

import { DATE_FORMAT_API_QUERY } from 'constants';
import { INTERVAL_LIST } from 'constants/lists';

import LightWeightBaseChart from './LightWeightBaseChart';

const getWhiteSpaceChartData = ({ from, to, interval }) => {
  const whiteSpaceData = [];
  const diff = to.diff(from, [interval.unit]).toObject();
  if (diff[interval.unit] > interval.quantity) {
    Array.from(
      {
        length: diff[interval.unit] / interval.quantity - interval.quantity,
      },
      (_1, i) => i + 1
    ).forEach((num) => {
      const time = from.plus({
        [interval.unit]: num * interval.quantity,
      });
      whiteSpaceData.push({ time: time.toMillis() });
    });
  }

  return whiteSpaceData;
};

const LightWeightPremiumKlineChart = forwardRef(
  (
    {
      baseAsset,
      alarmConfig,
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

    const alarmEntryPriceLineRef = useRef();
    const alarmExitPriceLineRef = useRef();

    const alarmEntrySeriesRef = useRef();
    const alarmExitSeriesRef = useRef();

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

    const showTether = useMemo(
      () =>
        alarmConfig?.isTether || alarmConfig?.entry || alarmConfig?.exit
          ? alarmConfig.isTether
          : isKimpExchange && isTetherPriceView,
      [alarmConfig, isKimpExchange, isTetherPriceView]
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

      if (showTether)
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
    }, [data?.[baseAsset], dataType, showTether]);

    const intervalValue = useMemo(
      () => INTERVAL_LIST.find((o) => o.value === interval),
      [interval]
    );

    const chartHistoricalData = useMemo(() => {
      const candlestick = [];
      const line = [];
      if (!dataType) return { candlestick, line };

      currentData?.forEach((item, index) => {
        const time = DateTime.fromISO(item.datetime_now);
        const open = item[`${dataType}_open`] || 0;
        const high = item[`${dataType}_high`] || 0;
        const low = item[`${dataType}_low`] || 0;
        const close = item[`${dataType}_close`] || 0;
        if (showTether)
          candlestick.push({
            time: time.toMillis(),
            open: item.dollar * (1 + open * 0.01),
            high: item.dollar * (1 + high * 0.01),
            low: item.dollar * (1 + low * 0.01),
            close: item.dollar * (1 + close * 0.01),
          });
        else
          candlestick.push({ time: time.toMillis(), open, high, low, close });
        if (item.tp !== null)
          line.push({ time: time.toMillis(), value: item.tp });

        if (currentData[index + 1]) {
          const timeNext = DateTime.fromISO(
            currentData[index + 1].datetime_now
          );
          const whiteSpaceData = getWhiteSpaceChartData({
            from: time,
            to: timeNext,
            interval: intervalValue,
          });
          candlestick.push(...whiteSpaceData);
          line.push(
            ...whiteSpaceData.map((d) => ({
              ...d,
              color: 'transparent',
              value: item.tp || undefined,
            }))
          );
        }
      });
      return { candlestick, line };
    }, [currentData, intervalValue, dataType, showTether]);

    useEffect(() => {
      if (alarmEntryPriceLineRef.current)
        candlestickSeriesRef.current?.removePriceLine(
          alarmEntryPriceLineRef.current
        );
      if (alarmExitPriceLineRef.current)
        candlestickSeriesRef.current?.removePriceLine(
          alarmExitPriceLineRef.current
        );
      if (isNumber(alarmConfig?.entry)) {
        alarmEntrySeriesRef.current?.setData([
          { time: DateTime.now().toMillis(), value: alarmConfig.entry },
        ]);
        alarmEntryPriceLineRef.current =
          candlestickSeriesRef.current?.createPriceLine({
            price: alarmConfig.entry,
            color: theme.palette.accent.main,
            lineWidth: 2,
            lineStyle: 0,
            axisLabelVisible: true,
            title: t('ENTRY'),
          });
      } else alarmEntrySeriesRef.current?.setData([]);
      if (isNumber(alarmConfig?.exit)) {
        alarmExitSeriesRef.current?.setData([
          { time: DateTime.now().toMillis(), value: alarmConfig.exit },
        ]);
        alarmExitPriceLineRef.current =
          candlestickSeriesRef.current?.createPriceLine({
            price: alarmConfig.exit,
            color: theme.palette.warning.main,
            lineWidth: 2,
            lineStyle: 0,
            axisLabelVisible: true,
            title: t('EXIT'),
          });
      } else alarmExitSeriesRef.current?.setData([]);
    }, [alarmConfig, interval, dataType, i18n.language]);

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
      candlestickSeriesRef.current?.applyOptions({
        priceFormat: {
          type: 'custom',
          formatter: (price) =>
            `${formatIntlNumber(price, 3, 3)} ${showTether ? t('KRW') : '%'}`,
        },
      });
      lineSeriesRef.current?.applyOptions({ title: t('Price') });
    }, [isMobile, showTether, i18n.language]);

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
                type: 'custom',
                formatter: (price) =>
                  `${formatIntlNumber(price, 3, 3)} ${
                    showTether ? t('KRW') : '%'
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
              type: 'price',
              precision: 2,
              minMove: 0.01,
            },
            title: t('Price'),
          });
          alarmEntrySeriesRef.current = baseChartRef.current.addLineSeries({
            color: 'transparent',
            lineWidth: 1,
          });
          alarmExitSeriesRef.current = baseChartRef.current.addLineSeries({
            color: 'transparent',
            lineWidth: 1,
          });
        }}
      />
    );
  }
);

export default React.memo(LightWeightPremiumKlineChart);
