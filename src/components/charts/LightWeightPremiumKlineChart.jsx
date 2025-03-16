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
import getWhiteSpaceChartData from 'utils/getWhiteSpaceChartData';

import { DATE_FORMAT_API_QUERY, USER_ROLE } from 'constants';
import { INTERVAL_LIST } from 'constants/lists';

import LightWeightBaseChart from './LightWeightBaseChart';

const LightWeightPremiumKlineChart = forwardRef(
  (
    {
      baseAsset,
      triggerConfig,
      dataType,
      chartMode = 'candlestick',
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
    const isAuthorized = loggedin && user.role !== USER_ROLE.visitor;

    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('md'));

    const { i18n, t } = useTranslation();

    const chartRef = useRef();

    const candlestickSeriesRef = useRef();
    const premiumLineSeriesRef = useRef();
    const lineSeriesRef = useRef();

    const triggerEntryPriceLineRef = useRef();
    const triggerExitPriceLineRef = useRef();

    const triggerEntrySeriesRef = useRef();
    const triggerExitSeriesRef = useRef();

    const refetchTimeoutRef = useRef();

    const [startTime, setStartTime] = useState(null);
    const [endTime, setEndTime] = useState(null);

    const [currentData, setCurrentData] = useState([]);
    const [loadedHistoricalData, setLoadedHistoricalData] = useState([]);
    const [preloadedData, setPreloadedData] = useState([]);

    const prevChartMode = usePrevious(chartMode);

    const [isChartReady, setIsChartReady] = useState(false);

    const reinitialize = () => {
      setStartTime(null);
      setEndTime(null);

      setCurrentData([]);
      setLoadedHistoricalData([]);
      setPreloadedData([]);

      if (candlestickSeriesRef.current) {
        try {
          candlestickSeriesRef.current.setData([]);
        } catch (e) {
          console.warn('Error clearing candlestick series:', e);
        }
      }
      
      if (premiumLineSeriesRef.current) {
        try {
          premiumLineSeriesRef.current.setData([]);
        } catch (e) {
          console.warn('Error clearing premium line series:', e);
        }
      }
      
      if (lineSeriesRef.current) {
        try {
          lineSeriesRef.current.setData([]);
        } catch (e) {
          console.warn('Error clearing line series:', e);
        }
      }
    };

    useImperativeHandle(
      ref,
      () => ({
        reinitialize,
        getChart: () => chartRef.current,
        getCandlestickSeries: () => candlestickSeriesRef.current,
        getLineSeries: () => lineSeriesRef.current,
        getPremiumLineSeries: () => premiumLineSeriesRef.current,
        getCurrentChartMode: () => chartMode,
      }),
      [chartMode]
    );

    const showTether = useMemo(
      () =>
        triggerConfig?.isTether || triggerConfig?.entry || triggerConfig?.exit
          ? triggerConfig.isTether
          : isKimpExchange && isTetherPriceView,
      [triggerConfig, isKimpExchange, isTetherPriceView]
    );

    const { data } = useGetRealTimeKlineQuery(
      {
        ...marketCodes,
        interval,
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

      const time = value.datetime_now / 1000;

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
          premiumLine: { time, value: value.dollar * (1 + close * 0.01) },
          line: value.tp !== null ? { time, value: value.tp } : undefined,
        };
      return {
        candlestick: { time, open, high, low, close },
        premiumLine: { time, value: close },
        line: value.tp !== null ? { time, value: value.tp } : undefined,
      };
    }, [data?.[baseAsset], dataType, showTether]);

    const intervalValue = useMemo(
      () => INTERVAL_LIST.find((o) => o.value === interval),
      [interval]
    );

    const chartHistoricalData = useMemo(() => {
      const candlestick = [];
      const premiumLine = [];
      const line = [];
      if (!dataType) return { candlestick, premiumLine, line };

      currentData?.forEach((item, index) => {
        const time = DateTime.fromISO(item.datetime_now);
        const open = item[`${dataType}_open`] || 0;
        const high = item[`${dataType}_high`] || 0;
        const low = item[`${dataType}_low`] || 0;
        const close = item[`${dataType}_close`] || 0;
        
        const timeMs = time.toMillis() / 1000;
        
        if (showTether) {
          candlestick.push({
            time: timeMs,
            open: item.dollar * (1 + open * 0.01),
            high: item.dollar * (1 + high * 0.01),
            low: item.dollar * (1 + low * 0.01),
            close: item.dollar * (1 + close * 0.01),
          });
          premiumLine.push({
            time: timeMs,
            value: item.dollar * (1 + close * 0.01),
          });
        } else {
          candlestick.push({
            time: timeMs,
            open,
            high,
            low,
            close,
          });
          premiumLine.push({
            time: timeMs,
            value: close,
          });
        }
        
        if (item.tp !== null)
          line.push({ time: timeMs, value: item.tp });
          
        const timeNext = currentData[index + 1]
          ? DateTime.fromISO(currentData[index + 1].datetime_now)
          : DateTime.now().minus({
              [intervalValue.unit]: intervalValue.quantity * 3,
            });
        const whiteSpaceData = getWhiteSpaceChartData({
          from: time,
          to: timeNext,
          interval: intervalValue,
        });
        
        candlestick.push(...whiteSpaceData);
        
        premiumLine.push(
          ...whiteSpaceData.map((d) => ({
            ...d,
            color: 'transparent',
            value: showTether ? item.dollar * (1 + close * 0.01) : close,
          }))
        );
        
        line.push(
          ...whiteSpaceData.map((d) => ({
            ...d,
            color: 'transparent',
            value: item.tp || undefined,
          }))
        );
      });
      
      return { candlestick, premiumLine, line };
    }, [currentData, intervalValue, dataType, showTether]);

    useEffect(() => {
      if (!isChartReady || !candlestickSeriesRef.current) return;
      
      try {
        if (triggerEntryPriceLineRef.current)
          candlestickSeriesRef.current.removePriceLine(
            triggerEntryPriceLineRef.current
          );
        if (triggerExitPriceLineRef.current)
          candlestickSeriesRef.current.removePriceLine(
            triggerExitPriceLineRef.current
          );
        if (triggerConfig?.entry || triggerConfig?.exit) {
          candlestickSeriesRef.current.applyOptions({ priceLineVisible: false });
          lineSeriesRef.current.applyOptions({ priceLineVisible: false });
        } else {
          candlestickSeriesRef.current.applyOptions({ priceLineVisible: true });
          lineSeriesRef.current.applyOptions({ priceLineVisible: true });
        }
        if (isNumber(triggerConfig?.entry)) {
          triggerEntrySeriesRef.current?.setData([
            {
              time: DateTime.now().toMillis() / 1000,
              value: triggerConfig.entry,
            },
          ]);
          triggerEntryPriceLineRef.current =
            candlestickSeriesRef.current.createPriceLine({
              price: triggerConfig.entry,
              color: theme.palette.accent.main,
              lineWidth: 1,
              lineStyle: 0,
              axisLabelVisible: true,
              title: t('ENTRY'),
            });
        } else {
          triggerEntrySeriesRef.current?.setData([]);
        }
        if (isNumber(triggerConfig?.exit)) {
          triggerExitSeriesRef.current?.setData([
            { time: DateTime.now().toMillis() / 1000, value: triggerConfig.exit },
          ]);
          triggerExitPriceLineRef.current =
            candlestickSeriesRef.current.createPriceLine({
              price: triggerConfig.exit,
              color: theme.palette.warning.main,
              lineWidth: 1,
              lineStyle: 0,
              axisLabelVisible: true,
              title: t('EXIT'),
            });
        } else triggerExitSeriesRef.current?.setData([]);
      } catch (e) {
        console.warn('Error updating trigger config:', e);
      }
    }, [triggerConfig, interval, dataType, i18n.language, isChartReady]);

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
      if (isChartReady && chartRef.current) {
        try {
          chartRef.current.timeScale().scrollToRealTime();
        } catch (e) {
          console.warn('Error scrolling to real time:', e);
        }
      }
    }, [interval, isChartReady]);

    const prevQueryKey = usePrevious(queryKey);
    useEffect(() => {
      if (isAuthorized)
        if (prevQueryKey !== null)
          if (prevQueryKey !== queryKey) refetchInitialData();
    }, [queryKey, isAuthorized]);

    useEffect(() => {
      if (!isChartReady || !candlestickSeriesRef.current || !premiumLineSeriesRef.current) return;
      
      try {
        if (chartMode === 'candlestick') {
          candlestickSeriesRef.current.applyOptions({ visible: true });
          premiumLineSeriesRef.current.applyOptions({ visible: false });
        } else {
          candlestickSeriesRef.current.applyOptions({ visible: false });
          premiumLineSeriesRef.current.applyOptions({ visible: true });
        }
        
        if (prevChartMode !== chartMode && chartHistoricalData.candlestick.length > 0) {
          if (chartRef.current && chartRef.current.timeScale) {
            chartRef.current.timeScale().fitContent();
          }
        }
      } catch (e) {
        console.warn('Error updating chart mode:', e);
      }
    }, [chartMode, prevChartMode, chartHistoricalData.candlestick.length, isChartReady]);

    useEffect(() => {
      if (!isChartReady || !candlestickSeriesRef.current || !premiumLineSeriesRef.current) return;
      
      try {
        candlestickSeriesRef.current.setData(chartHistoricalData.candlestick);
        premiumLineSeriesRef.current.setData(chartHistoricalData.premiumLine);
        lineSeriesRef.current.setData(chartHistoricalData.line);
      } catch (e) {
        console.warn('Error setting chart data:', e);
      }
    }, [chartHistoricalData, isChartReady]);

    useEffect(() => {
      if (
        !isFetchingInitialData &&
        !isFetchingHistoricalData &&
        chartRealTimeData &&
        candlestickSeriesRef.current &&
        premiumLineSeriesRef.current
      ) {
        if (chartRealTimeData.candlestick) {
          candlestickSeriesRef.current.update(chartRealTimeData.candlestick);
        }
        if (chartRealTimeData.premiumLine) {
          premiumLineSeriesRef.current.update(chartRealTimeData.premiumLine);
        }
        if (chartRealTimeData.line) {
          lineSeriesRef.current.update(chartRealTimeData.line);
        }
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

    useEffect(() => {
      if (chartMode) {
        try {
          localStorage.setItem(`${baseAsset}_chart_mode`, chartMode);
        } catch (error) {
          // Ignore storage errors
        }
      }
    }, [chartMode, baseAsset]);

    useEffect(() => {
      try {
        const storedChartMode = localStorage.getItem(`${baseAsset}_chart_mode`);
        if (storedChartMode && (storedChartMode === 'candlestick' || storedChartMode === 'line')) {
          // We don't directly call setChartMode here to avoid conflicts
          // The parent component (PremiumDataChartViewer) should read this and set the mode
        }
      } catch (error) {
        // Ignore storage errors
      }
    }, [baseAsset]);

    useEffect(() => () => {
      if (refetchTimeoutRef.current) {
        clearTimeout(refetchTimeoutRef.current);
      }
      
      setIsChartReady(false);
      
      candlestickSeriesRef.current = null;
      premiumLineSeriesRef.current = null;
      lineSeriesRef.current = null;
      triggerEntrySeriesRef.current = null;
      triggerExitSeriesRef.current = null;
      triggerEntryPriceLineRef.current = null;
      triggerExitPriceLineRef.current = null;
    }, []);

    const candlestickSeriesOptions = useMemo(() => ({
      priceScaleId: 'right',
      downColor: theme.palette.error.main,
      upColor: theme.palette.success.main,
      wickDownColor: theme.palette.error.main,
      wickUpColor: theme.palette.success.main,
      priceLineVisible: false,
      priceFormat: {
        type: 'custom',
        formatter: (price) =>
          `${formatIntlNumber(price, 3, 3)} ${
            showTether ? t('KRW') : '%'
          }`,
      },
      visible: chartMode === 'candlestick'
    }), [theme.palette, showTether, t, chartMode]);

    const premiumLineSeriesOptions = useMemo(() => ({
      priceScaleId: 'right',
      color: theme.palette.accent.main,
      crosshairMarkerVisible: true,
      lineType: LineType.Curved,
      lineWidth: 1.25,
      priceFormat: {
        type: 'custom',
        formatter: (price) =>
          `${formatIntlNumber(price, 3, 3)} ${
            showTether ? t('KRW') : '%'
          }`,
      },
      priceLineVisible: false,
      visible: chartMode === 'line'
    }), [theme.palette, showTether, t, chartMode]);

    return (
      <LightWeightBaseChart
        ref={chartRef}
        baseSeriesRef={chartMode === 'candlestick' ? candlestickSeriesRef : premiumLineSeriesRef}
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
        sx={{ marginBottom: 0 }}
        onBarsInfoChanged={({ start, end }) => {
          if (!isFetchingHistoricalData && isChartReady) {
            setEndTime(end.toFormat(DATE_FORMAT_API_QUERY));
            setStartTime(
              start.startOf('minute').toFormat(DATE_FORMAT_API_QUERY)
            );
          }
        }}
        onReady={(baseChartRef) => {
          if (!baseChartRef.current) return;
          
          try {
            candlestickSeriesRef.current =
              baseChartRef.current.addCandlestickSeries(candlestickSeriesOptions);
              
            premiumLineSeriesRef.current = baseChartRef.current.addLineSeries(premiumLineSeriesOptions);
            
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
              priceLineVisible: false,
              title: t('Price'),
            });
            
            candlestickSeriesRef.current.applyOptions({ 
              visible: chartMode === 'candlestick' 
            });
            premiumLineSeriesRef.current.applyOptions({ 
              visible: chartMode === 'line' 
            });
            
            triggerEntrySeriesRef.current = baseChartRef.current.addLineSeries({
              color: 'transparent',
              lineWidth: 1,
            });
            triggerExitSeriesRef.current = baseChartRef.current.addLineSeries({
              color: 'transparent',
              lineWidth: 1,
            });
            
            setIsChartReady(true);
          } catch (e) {
            console.error('Error initializing chart:', e);
          }
        }}
      />
    );
  }
);

export default React.memo(LightWeightPremiumKlineChart);
