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
    const [preloadBuffer, setPreloadBuffer] = useState([]);
    const [isPreloading, setIsPreloading] = useState(false);

    const prevChartMode = usePrevious(chartMode);

    const [isChartReady, setIsChartReady] = useState(false);

    const intervalValue = useMemo(
      () => INTERVAL_LIST.find((o) => o.value === interval),
      [interval]
    );

    const initialViewAppliedRef = useRef(false);

    const dataTypeChangingRef = useRef(false);
    const prevDataTypeRef = useRef(dataType);

    const [isPremiumTypeChanging, setIsPremiumTypeChanging] = useState(false);

    const reinitialize = () => {
      setStartTime(null);
      setEndTime(null);
      initialViewAppliedRef.current = false;

      setCurrentData([]);
      setLoadedHistoricalData([]);
      setPreloadedData([]);

      if (candlestickSeriesRef.current) {
        try {
          candlestickSeriesRef.current.setData([]);
        } catch (e) {
          // console.warn('Error clearing candlestick series:', e);
        }
      }
      
      if (premiumLineSeriesRef.current) {
        try {
          premiumLineSeriesRef.current.setData([]);
        } catch (e) {
          // console.warn('Error clearing premium line series:', e);
        }
      }
      
      if (lineSeriesRef.current) {
        try {
          lineSeriesRef.current.setData([]);
        } catch (e) {
          // console.warn('Error clearing line series:', e);
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
        getCurrentChartDataType: () => dataType,
      }),
      [chartMode, dataType]
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

    const {
      currentData: preloadData,
      isFetching: isFetchingPreloadData,
    } = useGetHistoricalKlineQuery(
      {
        ...marketCodes,
        baseAsset,
        startTime: startTime ? 
          DateTime.fromFormat(startTime, DATE_FORMAT_API_QUERY)
            .minus({ [intervalValue?.unit || 'minutes']: (intervalValue?.quantity || 1) * 200 })
            .toFormat(DATE_FORMAT_API_QUERY) : 
          null,
        endTime: startTime,
        interval,
        tz: timezone,
      },
      {
        skip: !isAuthorized || !marketCodes || !startTime || !intervalValue || isPreloading,
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

    // Completely rewrite the updateTriggerPriceLines function to be more reliable
    const updateTriggerPriceLines = () => {
      if (!isChartReady || 
          !candlestickSeriesRef.current || 
          !premiumLineSeriesRef.current) return;
      
      try {
        // Always clear previous price lines from both series
        if (triggerEntryPriceLineRef.current) {
          try {
            candlestickSeriesRef.current.removePriceLine(triggerEntryPriceLineRef.current);
          } catch (e) { /* ignore */ }
          
          try {
            premiumLineSeriesRef.current.removePriceLine(triggerEntryPriceLineRef.current);
          } catch (e) { /* ignore */ }
          
          triggerEntryPriceLineRef.current = null;
        }
        
        if (triggerExitPriceLineRef.current) {
          try {
            candlestickSeriesRef.current.removePriceLine(triggerExitPriceLineRef.current);
          } catch (e) { /* ignore */ }
          
          try {
            premiumLineSeriesRef.current.removePriceLine(triggerExitPriceLineRef.current);
          } catch (e) { /* ignore */ }
          
          triggerExitPriceLineRef.current = null;
        }
        
        // Select the currently active series
        const activeSeries = chartMode === 'candlestick' ? 
          candlestickSeriesRef.current : 
          premiumLineSeriesRef.current;
        
        // Add entry price line if needed
        if (isNumber(triggerConfig?.entry)) {
          triggerEntryPriceLineRef.current = activeSeries.createPriceLine({
            price: triggerConfig.entry,
            color: theme.palette.accent.main,
            lineWidth: 1,
            lineStyle: 0,
            axisLabelVisible: true,
            title: t('ENTRY'),
          });
        }
        
        // Add exit price line if needed
        if (isNumber(triggerConfig?.exit)) {
          triggerExitPriceLineRef.current = activeSeries.createPriceLine({
            price: triggerConfig.exit,
            color: theme.palette.warning.main,
            lineWidth: 1,
            lineStyle: 0,
            axisLabelVisible: true,
            title: t('EXIT'),
          });
        }
      } catch (e) {
        // console.warn('Error updating trigger price lines:', e);
      }
    };

    // Replace the trigger config effect
    useEffect(() => {
      if (triggerConfig?.entry || triggerConfig?.exit) {
        // Short delay to ensure chart is rendered
        setTimeout(updateTriggerPriceLines, 50);
      }
    }, [triggerConfig, chartMode, i18n.language, isChartReady]);

    // Update chart data effect - make sure we reapply trigger lines
    useEffect(() => {
      if (!isChartReady || 
          !candlestickSeriesRef.current || 
          !premiumLineSeriesRef.current ||
          !lineSeriesRef.current) return;
      
      try {
        // Handle data type change differently - prevent flickering
        if (prevDataTypeRef.current !== dataType && dataType && isChartReady) {
          // Set loading state to true when premium type changes
          setIsPremiumTypeChanging(true);
          
          // Schedule the data update with a delay to ensure complete transition
          setTimeout(() => {
            try {
              if (chartRef.current && 
                  candlestickSeriesRef.current && 
                  premiumLineSeriesRef.current &&
                  lineSeriesRef.current) {
                
                // Apply data all at once
                candlestickSeriesRef.current.setData(chartHistoricalData.candlestick);
                premiumLineSeriesRef.current.setData(chartHistoricalData.premiumLine);
                lineSeriesRef.current.setData(chartHistoricalData.line);
                
                // Apply font and other styling as a complete update
                chartRef.current.applyOptions({
                  layout: {
                    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
                    fontSize: isMobile ? 10 : 12,
                    textColor: theme.palette.text.primary,
                  },
                  timeScale: {
                    borderColor: theme.palette.divider,
                    timeVisible: true,
                    secondsVisible: false,
                    rightOffset: 5,
                    rightBarStaysOnScroll: true
                  },
                  grid: {
                    vertLines: { color: theme.palette.divider },
                    horzLines: { color: theme.palette.divider },
                  }
                });
                
                // Set the visible range
                const timeScale = chartRef.current.timeScale();
                const totalBars = chartHistoricalData.candlestick.length;
                const barsToShow = Math.min(totalBars, 150);
                
                timeScale.setVisibleLogicalRange({
                  from: Math.max(0, totalBars - barsToShow),
                  to: totalBars
                });
                
                // Apply all series styling
                candlestickSeriesRef.current.applyOptions({
                  visible: chartMode === 'candlestick',
                  priceFormat: {
                    type: 'custom',
                    formatter: (price) => 
                      `${formatIntlNumber(price, 3, 3)} ${showTether ? t('KRW') : '%'}`,
                  }
                });
                
                premiumLineSeriesRef.current.applyOptions({
                  visible: chartMode === 'line',
                  priceFormat: {
                    type: 'custom',
                    formatter: (price) => 
                      `${formatIntlNumber(price, 3, 3)} ${showTether ? t('KRW') : '%'}`,
                  }
                });
                
                lineSeriesRef.current.applyOptions({
                  priceFormat: {
                    type: 'price',
                    precision: 2,
                    minMove: 0.01,
                  },
                  lastValueVisible: true,
                  title: 'KRW',
                });
                
                // Update trigger lines if needed
                if (triggerConfig?.entry || triggerConfig?.exit) {
                  updateTriggerPriceLines();
                }
              }
              
              // Reset the loading state and update refs
              prevDataTypeRef.current = dataType;
              setIsPremiumTypeChanging(false);
            } catch (e) {
              // console.warn('Error during premium type change:', e);
              setIsPremiumTypeChanging(false);
            }
          }, 100);  // Delay to ensure clean transition
        } else if (!dataTypeChangingRef.current) {
          // Normal case - no data type change
          candlestickSeriesRef.current.setData(chartHistoricalData.candlestick);
          premiumLineSeriesRef.current.setData(chartHistoricalData.premiumLine);
          lineSeriesRef.current.setData(chartHistoricalData.line);
          
          // Make sure visibility is correct
          candlestickSeriesRef.current.applyOptions({ 
            visible: chartMode === 'candlestick' 
          });
          
          premiumLineSeriesRef.current.applyOptions({ 
            visible: chartMode === 'line' 
          });
          
          // Reapply trigger lines
          if (triggerConfig?.entry || triggerConfig?.exit) {
            setTimeout(updateTriggerPriceLines, 50);
          }
        }
        
        // Set right margin to 5 bars
        if (chartRef.current) {
          chartRef.current.timeScale().applyOptions({
            rightOffset: 5,
            rightBarStaysOnScroll: true
          });
        }
      } catch (e) {
        // console.warn('Error setting chart data:', e);
      }
    }, [chartHistoricalData, isChartReady, chartMode, dataType]);

    // Modify chart mode effect to properly handle mode changes
    useEffect(() => {
      if (!isChartReady || !candlestickSeriesRef.current || !premiumLineSeriesRef.current) return;
      
      try {
        // Update visibility
        candlestickSeriesRef.current.applyOptions({ 
          visible: chartMode === 'candlestick' 
        });
        
        premiumLineSeriesRef.current.applyOptions({ 
          visible: chartMode === 'line' 
        });
        
        // If chart mode changed, fit content
        if (prevChartMode !== chartMode && chartHistoricalData.candlestick.length > 0) {
          if (chartRef.current && chartRef.current.timeScale) {
            chartRef.current.timeScale().fitContent();
            
            // Ensure rightOffset is maintained after content is fit
            chartRef.current.timeScale().applyOptions({
              rightOffset: 5,
              rightBarStaysOnScroll: true
            });
          }
        }
        
        // Always reapply trigger lines after mode change
        if (triggerConfig?.entry || triggerConfig?.exit) {
          setTimeout(updateTriggerPriceLines, 100);
        }
      } catch (e) {
        // console.warn('Error updating chart mode:', e);
      }
    }, [chartMode, prevChartMode, isChartReady]);

    useEffect(() => {
      setLoadedHistoricalData((state) => [...(historicalData || []), ...state]);
      if (isSuccessHistoricalData && historicalData?.length === 0) {
        setStartTime(null);
        setEndTime(null);
      }
    }, [historicalData, isSuccessHistoricalData]);

    useEffect(() => {
      if (preloadData && preloadData.length > 0) {
        setLoadedHistoricalData(state => [...preloadData, ...state]);
        
        if (startTime && intervalValue) {
          const preloadStartTime = DateTime.fromFormat(startTime, DATE_FORMAT_API_QUERY)
            .minus({ [intervalValue.unit]: intervalValue.quantity * 50 })
            .toFormat(DATE_FORMAT_API_QUERY);
          
          setPreloadBuffer(prev => [
            ...prev, 
            { start: preloadStartTime, end: startTime }
          ]);
        }
        
        setIsPreloading(false);
      }
    }, [preloadData, startTime, intervalValue]);

    useEffect(() => {
      if (startTime && !isPreloading) {
        setIsPreloading(true);
      }
    }, [startTime]);

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
      if (!isChartReady || 
          !candlestickSeriesRef.current || 
          !premiumLineSeriesRef.current ||
          !lineSeriesRef.current || 
          !chartRealTimeData) return;
      
      try {
        // Apply real-time data to each series
        if (chartRealTimeData.candlestick) {
          candlestickSeriesRef.current.update(chartRealTimeData.candlestick);
        }
        
        if (chartRealTimeData.premiumLine) {
          premiumLineSeriesRef.current.update(chartRealTimeData.premiumLine);
        }
        
        if (chartRealTimeData.line) {
          lineSeriesRef.current.update(chartRealTimeData.line);
        }
      } catch (e) {
        // console.warn('Error updating real-time data:', e);
      }
    }, [chartRealTimeData, isChartReady]);

    // Add this useEffect to specifically handle the initial chart view
    useEffect(() => {
      if (isChartReady && 
          chartRef.current && 
          chartHistoricalData.candlestick.length > 0) {
        
        try {
          const timeScale = chartRef.current.timeScale();
          
          if (!initialViewAppliedRef.current) {
            const totalBars = chartHistoricalData.candlestick.length;
            const barsToShow = Math.min(totalBars, 150);
            
            timeScale.setVisibleLogicalRange({
              from: Math.max(0, totalBars - barsToShow),
              to: totalBars
            });
            
            // Add this line to ensure rightOffset is applied during initial setup
            timeScale.applyOptions({
              rightOffset: 5,
              rightBarStaysOnScroll: true
            });
            
            initialViewAppliedRef.current = true;
          } else {
            timeScale.scrollToRealTime();
            
            // Also maintain the right offset when scrolling to real time
            timeScale.applyOptions({
              rightOffset: 5,
              rightBarStaysOnScroll: true
            });
          }
        } catch (e) {
          // console.warn('Error setting chart view:', e);
        }
      }
    }, [isChartReady, chartHistoricalData.candlestick.length]);

    useEffect(() => {
      if (interval) {
        initialViewAppliedRef.current = false;
        prevDataTypeRef.current = dataType; // Reset the data type tracking on interval change
      }
    }, [interval, dataType]);

    const prevQueryKey = usePrevious(queryKey);
    useEffect(() => {
      if (isAuthorized)
        if (prevQueryKey !== null)
          if (prevQueryKey !== queryKey) refetchInitialData();
    }, [queryKey, isAuthorized]);

    useEffect(() => {
      if (refetchTimeoutRef.current) clearTimeout(refetchTimeoutRef.current);
    }, [interval, dataType, marketCodes]);

    useEffect(() => {
      if (!isChartReady || !candlestickSeriesRef.current || !premiumLineSeriesRef.current) return;
      
      try {
        candlestickSeriesRef.current.applyOptions({
          priceFormat: {
            type: 'custom',
            formatter: (price) =>
              `${formatIntlNumber(price, 3, 3)} ${showTether ? t('KRW') : '%'}`,
          }
        });
        
        premiumLineSeriesRef.current.applyOptions({
          priceFormat: {
            type: 'custom',
            formatter: (price) =>
              `${formatIntlNumber(price, 3, 3)} ${showTether ? t('KRW') : '%'}`,
          },
          visible: chartMode === 'line'
        });
        
        lineSeriesRef.current?.applyOptions({ title: t('Price') });
      } catch (e) {
        // console.warn('Error updating price format:', e);
      }
    }, [isMobile, showTether, i18n.language, isChartReady]);

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

    useEffect(() => {
      if (!isChartReady || !chartRef.current) {
        // Always return a function, even in the early return case
        return () => {
          // Empty cleanup function
        };
      }
      
      // Apply the rightOffset with a delay to ensure it happens after any data changes
      const applyRightOffset = () => {
        try {
          if (chartRef.current) {
            chartRef.current.timeScale().applyOptions({
              rightOffset: 5,
              rightBarStaysOnScroll: true
            });
          }
        } catch (e) {
          // console.warn('Error applying right offset:', e);
        }
      };
      
      // Apply immediately 
      applyRightOffset();
      
      // And also with some delay to ensure it happens after any internal chart updates
      const timeout1 = setTimeout(applyRightOffset, 100);
      const timeout2 = setTimeout(applyRightOffset, 500);
      const timeout3 = setTimeout(applyRightOffset, 1000); // Add a longer timeout for good measure
      
      // Return cleanup function
      return () => {
        clearTimeout(timeout1);
        clearTimeout(timeout2);
        clearTimeout(timeout3);
      };
    }, [dataType, isChartReady]);

    const candlestickSeriesOptions = useMemo(() => ({
      priceScaleId: 'right',
      downColor: theme.palette.error.main,
      upColor: theme.palette.success.main,
      wickDownColor: theme.palette.error.main,
      wickUpColor: theme.palette.success.main,
      priceLineVisible: true,
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
      lineWidth: isMobile ? 0.7 : 1,
      priceFormat: {
        type: 'custom',
        formatter: (price) =>
          `${formatIntlNumber(price, 3, 3)} ${
            showTether ? t('KRW') : '%'
          }`,
      },
      priceLineVisible: true,
      visible: chartMode === 'line',
    }), [theme.palette, showTether, t, isMobile, chartMode]);

    const handleBarsInfoChanged = ({ start, end }) => {
      if (!isFetchingHistoricalData && !isFetchingPreloadData && isChartReady) {
        const endTimeFormatted = end.toFormat(DATE_FORMAT_API_QUERY);
        const startTimeFormatted = start.startOf('minute').toFormat(DATE_FORMAT_API_QUERY);
        
        const isInPreloadBuffer = preloadBuffer.some(range => 
          DateTime.fromFormat(range.start, DATE_FORMAT_API_QUERY) <= start &&
          DateTime.fromFormat(range.end, DATE_FORMAT_API_QUERY) >= end
        );
        
        if (!isInPreloadBuffer) {
          setEndTime(endTimeFormatted);
          setStartTime(startTimeFormatted);
        }
      }
    };

    const onReady = (baseChartRef) => {
      if (!baseChartRef.current) return;
      
      try {
        // Apply font settings explicitly to the chart
        baseChartRef.current.applyOptions({
          layout: {
            fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
            fontSize: isMobile ? 10 : 12,
            textColor: theme.palette.text.primary,
          },
          timeScale: {
            borderColor: theme.palette.divider,
            timeVisible: true,
            secondsVisible: false,
            rightOffset: 5, // Changed from 50 to 5 for consistency
            rightBarStaysOnScroll: true
          }
        });
        
        candlestickSeriesRef.current =
          baseChartRef.current.addCandlestickSeries(candlestickSeriesOptions);
          
        premiumLineSeriesRef.current = baseChartRef.current.addLineSeries(premiumLineSeriesOptions);
        
        lineSeriesRef.current = baseChartRef.current.addLineSeries({
          priceScaleId: 'left',
          color: theme.palette.primary.main,
          crosshairMarkerVisible: true,
          lineType: LineType.Curved,
          lineWidth: isMobile ? 0.7 : 1,
          priceFormat: {
            type: 'price',
            precision: 2,
            minMove: 0.01,
          },
          priceLineVisible: true,
          lastValueVisible: true,
          title: '',
        });
        
        candlestickSeriesRef.current.applyOptions({ 
          visible: chartMode === 'candlestick',
        });
        
        premiumLineSeriesRef.current.applyOptions({ 
          visible: chartMode === 'line',
        });
        
        triggerEntrySeriesRef.current = baseChartRef.current.addLineSeries({
          color: 'transparent',
          lineWidth: 1,
          lastValueVisible: false,
        });
        
        triggerExitSeriesRef.current = baseChartRef.current.addLineSeries({
          color: 'transparent',
          lineWidth: 1,
          lastValueVisible: false,
        });
        
        setIsChartReady(true);
        
        if (triggerConfig?.entry || triggerConfig?.exit) {
          setTimeout(updateTriggerPriceLines, 200);
        }
      } catch (e) {
        console.error('Error initializing chart:', e);
      }
    };

    useEffect(() => {
      if (!isChartReady || !lineSeriesRef.current) return;
      
      try {
        lineSeriesRef.current.applyOptions({
          visible: true,
          lastValueVisible: true,
          title: t('Price'),
          priceLineVisible: true,
          color: theme.palette.primary.main,
          lineWidth: isMobile ? 0.85 : 1,
        });
        
        if (chartHistoricalData.line.length > 0) {
          lineSeriesRef.current.setData(chartHistoricalData.line);
        }
      } catch (e) {
        // console.warn('Error updating price line options:', e);
      }
    }, [isChartReady, chartHistoricalData.line, isMobile, theme.palette]);

    useEffect(() => {
      if (dataType && initialViewAppliedRef.current && isChartReady && chartRef.current) {
        try {
          setTimeout(() => {
            const timeScale = chartRef.current.timeScale();
            const totalBars = chartHistoricalData.candlestick.length;
            
            const barsToShow = Math.min(totalBars, 150);
            
            timeScale.setVisibleLogicalRange({
              from: Math.max(0, totalBars - barsToShow),
              to: totalBars
            });
            
            // Maintain rightOffset after setting the visible range
            timeScale.applyOptions({
              rightOffset: 5,
              rightBarStaysOnScroll: true
            });
          }, 100);
        } catch (e) {
          // console.warn('Error resetting chart view after data type change:', e);
        }
      }
    }, [dataType, isChartReady]);

    const chartOptions = {
      leftPriceScale: { visible: true },
      rightPriceScale: { visible: true },
      handleScale: isAuthorized,
      handleScroll: isAuthorized,
      // Ensure consistent font styling with explicit sizing
      layout: {
        fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
        fontSize: isMobile ? 10 : 12,
        textColor: theme.palette.text.primary,
      },
      timeScale: {
        borderColor: theme.palette.divider,
        timeVisible: true,
        secondsVisible: false,
      },
      grid: {
        vertLines: {
          color: theme.palette.divider,
        },
        horzLines: {
          color: theme.palette.divider,
        },
      },
    };

    return (
      <LightWeightBaseChart
        ref={chartRef}
        baseSeriesRef={chartMode === 'candlestick' ? candlestickSeriesRef : premiumLineSeriesRef}
        chartOptions={chartOptions}
        dependencies={[marketCodes, interval, dataType]}
        interval={intervalValue}
        isLoading={
          isLoadingInitialData ||
          (isFetchingInitialData && preloadedData.length === 0) ||
          isFetchingHistoricalData ||
          isFetchingPreloadData
        }
        isUnauthorized={!isAuthorized}
        sx={{ marginBottom: 0 }}
        onBarsInfoChanged={handleBarsInfoChanged}
        onReady={onReady}
      />
    );
  }
);

export default React.memo(LightWeightPremiumKlineChart);
