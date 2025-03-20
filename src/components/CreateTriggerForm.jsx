import React, {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from 'react';

import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Checkbox from '@mui/material/Checkbox';
import CircularProgress from '@mui/material/CircularProgress';
import Divider from '@mui/material/Divider';
import FormControl from '@mui/material/FormControl';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormHelperText from '@mui/material/FormHelperText';
import FormLabel from '@mui/material/FormLabel';
import Grid from '@mui/material/Grid';
import Input from '@mui/material/Input';
import InputAdornment from '@mui/material/InputAdornment';
import InputLabel from '@mui/material/InputLabel';
import LinearProgress from '@mui/material/LinearProgress';
import OutlinedInput from '@mui/material/OutlinedInput';
import Slider from '@mui/material/Slider';
import Snackbar from '@mui/material/Snackbar';
import Stack from '@mui/material/Stack';
import Switch from '@mui/material/Switch';
import TextField from '@mui/material/TextField';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Typography from '@mui/material/Typography';

import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import PaymentIcon from '@mui/icons-material/Payment';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';

import { useTheme } from '@mui/material/styles';

import { LineStyle, LineType } from 'lightweight-charts';

import { Controller, useForm, useWatch } from 'react-hook-form';

import { useTranslation } from 'react-i18next';

import { useSelector } from 'react-redux';

import { useGetDollarQuery } from 'redux/api/drf/infocore';
import {
  useGetExchangeApiKeyQuery,
  useLazyGetPBoundaryQuery,
  usePostRepeatTradeMutation,
  usePostTradeMutation,
  usePostTradeConfigMutation,
} from 'redux/api/drf/tradecore';

import { DateTime } from 'luxon';

import { usePrevious } from '@uidotdev/usehooks';

import isKoreanMarket from 'utils/isKoreanMarket';

import NumberFormatWrapper from 'components/NumberFormatWrapper';
import formatIntlNumber from 'utils/formatIntlNumber';

const CreateTriggerForm = forwardRef(
  (
    {
      baseAsset,
      marketCodes,
      interval,
      isTetherPriceView,
      tradeConfigAllocation,
      tradeType,
      onTriggerConfigChange,
      onCreateSuccess,
      premiumDataViewerRef,
    },
    ref
  ) => {
    const predictionSeriesRef = useRef();
    const regressionLineSeriesRef = useRef();
    const lastPBoundaryRef = useRef(null); // Store the last successful pBoundary

    const { i18n, t } = useTranslation();

    const theme = useTheme();

    const user = useSelector((state) => state.auth.user);

    const [alertMessage, setAlertMessage] = useState(null);
    const [apiKeys, setApiKeys] = useState();
    const [autoRepeat, setAutoRepeat] = useState(0);
    const [disabled, setDisabled] = useState(false);
    const [setup, setSetup] = useState('manual');
    const [pBoundaryState, setPBoundary] = useState(null);

    // Add state to track chart tab changes
    const [lastChartDataType, setLastChartDataType] = useState(null);

    // Instead of trying to maintain references to chart series, store the data itself
    const [pBoundaryData, setPBoundaryData] = useState(null);
    const chartDataRef = useRef({
      chartReady: false,
      regressionSeries: null,
      predictionSeries: null,
    });

    useImperativeHandle(
      ref,
      () => ({
        setDisabled,
      }),
      []
    );

    const showTether = useMemo(
      () =>
        (isKoreanMarket(marketCodes?.targetMarketCode) &&
          !isKoreanMarket(marketCodes?.originMarketCode)) ||
        (!isKoreanMarket(marketCodes?.targetMarketCode) &&
          isKoreanMarket(marketCodes?.originMarketCode)),
      [marketCodes]
    );

    const autoSetupForm = useForm({
      defaultValues: { klineNum: 200, interval, percentGap: 1 },
      mode: 'all',
    });
    const { isValid: isSetupValid, submitCount: setupSubmitCount } =
      autoSetupForm.formState;

    const {
      control,
      formState,
      getValues,
      handleSubmit,
      reset,
      setValue,
      trigger,
    } = useForm({
      defaultValues: {
        entry: '',
        exit: '',
        tradeCapital: tradeType === 'autoTrade' ? '' : undefined,
        isTether: isTetherPriceView || false,
      },
      mode: 'all',
    });

    const { isDirty, isValid } = formState;

    const entry = useWatch({ control, name: 'entry' });
    const exit = useWatch({ control, name: 'exit' });
    const isTether = useWatch({ control, name: 'isTether' });

    const {
      data: exchangeApiKey,
      isError,
      isFetching,
      isSuccess,
    } = useGetExchangeApiKeyQuery(
      { tradeConfigUuid: tradeConfigAllocation?.trade_config_uuid },
      {
        skip: tradeType !== 'autoTrade',
      }
    );

    const {
      data: dollar,
      isFetching: isDollarFetching,
      isSuccess: isDollarSuccess,
    } = useGetDollarQuery({}, { skip: !isTether });

    const [postRepeatTrade] = usePostRepeatTradeMutation();
    const [postTrade, tradeResults] = usePostTradeMutation();
    const [postTradeConfig, tradeConfigResults] = usePostTradeConfigMutation();

    const [
      getPBoundary,
      {
        isFetching: isPBoundaryFetching,
        isSuccess: isPBoundarySuccess,
        data: pBoundary,
      },
    ] = useLazyGetPBoundaryQuery();

    const isLoading = tradeResults.isLoading || tradeConfigResults.isLoading;

    const onCalculate = async (data) => {
      if (!tradeConfigAllocation) {
        try {
          const results = await postTradeConfig({
            acw_user_uuid: user?.uuid,
            target_market_code: marketCodes?.targetMarketCode,
            origin_market_code: marketCodes?.originMarketCode,
          }).unwrap();
          getPBoundary({
            baseAsset,
            interval,
            marketCodeCombination: `${marketCodes.targetMarketCode}:${marketCodes.originMarketCode}`,
            tradeConfigUuid: results.uuid,
            usdtConversion: isTether,
            ...data,
          });
        } catch (err) {
          setAlertMessage({
            message: t('An error occurred. Please try again.'),
            status: 'error',
          });
        }
      } else
        getPBoundary({
          baseAsset,
          interval,
          marketCodeCombination: `${marketCodes.targetMarketCode}:${marketCodes.originMarketCode}`,
          tradeConfigUuid: tradeConfigAllocation.trade_config_uuid,
          usdtConversion: isTether,
          ...data,
        });
    };

    const onSubmit = async (data) => {
      const autoSetupValues = autoSetupForm.getValues();

      try {
        let trade;
        let tradeConfigUuid = tradeConfigAllocation?.trade_config_uuid;
        if (isValid)
          if (!tradeConfigAllocation) {
            const results = await postTradeConfig({
              acw_user_uuid: user?.uuid,
              target_market_code: marketCodes?.targetMarketCode,
              origin_market_code: marketCodes?.originMarketCode,
            }).unwrap();
            tradeConfigUuid = results.uuid;
            trade = await postTrade({
              base_asset: baseAsset,
              trade_config_uuid: results.uuid,
              usdt_conversion: data.isTether,
              low: parseFloat(data.entry),
              high: parseFloat(data.exit),
              trade_capital:
                tradeType === 'autoTrade'
                  ? parseInt(data.tradeCapital.replace(/,/g, ''), 10)
                  : undefined,
              trade_switch: tradeType === 'autoTrade' ? 0 : undefined,
            }).unwrap();
          } else
            trade = await postTrade({
              base_asset: baseAsset,
              trade_config_uuid: tradeConfigAllocation.trade_config_uuid,
              usdt_conversion: data.isTether,
              low: parseFloat(data.entry),
              high: parseFloat(data.exit),
              trade_capital:
                tradeType === 'autoTrade'
                  ? parseInt(data.tradeCapital.replace(/,/g, ''), 10)
                  : undefined,
              trade_switch: tradeType === 'autoTrade' ? 0 : undefined,
            }).unwrap();
        if (autoRepeat && trade)
          postRepeatTrade({
            trade_config_uuid: tradeConfigUuid,
            trade_uuid: trade.uuid,
            kline_interval: interval,
            kline_num: autoSetupValues?.klineNum,
            auto_repeat_num: 0, // TODO: Replace with actual value
            pauto_num: autoSetupValues?.percentGap,
            auto_repeat_switch: autoRepeat,
          });
      } catch (e) {
        setAlertMessage({
          message: t('An error occurred. Please try again.'),
          status: 'error',
        });
      }
    };

    useEffect(() => {
      if (tradeResults.isSuccess) {
        reset();
        autoSetupForm.reset();
        setAutoRepeat(0);
        setSetup('manual');
        setAlertMessage({
          message: t('Successfully registered trigger.'),
          status: 'success',
        });
        if (onCreateSuccess) onCreateSuccess(tradeResults);
      } else if (tradeResults.isError) {
        setAlertMessage({
          message: t('An error occurred. Please try again.'),
          status: 'error',
        });
      }
    }, [tradeResults]);

    useEffect(() => {
      if (entry && exit) trigger(['entry', 'exit']);
      onTriggerConfigChange({
        entry: entry ? parseFloat(entry) : null,
        exit: exit ? parseFloat(exit) : null,
        isTether,
      });
    }, [entry, exit, isTether]);

    useEffect(() => {
      if (setup === 'manual')
        if (dollar && isDollarSuccess) {
          const entryValue = getValues('entry');
          if (entryValue && parseFloat(entryValue) <= 500)
            setValue(
              'entry',
              (dollar.price * (1 + parseFloat(entryValue) / 100)).toFixed(3)
            );
          const exitValue = getValues('exit');
          if (exitValue && parseFloat(exitValue) <= 500)
            setValue(
              'exit',
              (dollar.price * (1 + parseFloat(exitValue) / 100)).toFixed(3)
            );
        }
    }, [dollar, isDollarSuccess, setup]);

    // Function to apply regression line and prediction points to the chart
    const applyVisualizationsToChart = (force = false) => {
      if (!pBoundaryData) return;
      
      // Get the current chart and verify it exists
      const klineChartRef = premiumDataViewerRef?.current?.getKlineChartRef();
      const chart = klineChartRef?.current?.getChart();
      if (!chart) return;
      
      // Get current trigger values
      const currentEntry = getValues('entry');
      const currentExit = getValues('exit');
      const parsedEntry = currentEntry ? parseFloat(currentEntry) : null;
      const parsedExit = currentExit ? parseFloat(currentExit) : null;
      
      // Always remove old series first to prevent duplicates
      try {
        if (chartDataRef.current.regressionSeries) {
          chart.removeSeries(chartDataRef.current.regressionSeries);
          chartDataRef.current.regressionSeries = null;
        }
        if (chartDataRef.current.predictionSeries) {
          chart.removeSeries(chartDataRef.current.predictionSeries);
          chartDataRef.current.predictionSeries = null;
        }
      } catch (error) {
        console.warn('Error removing old series', error);
        // Continue even if removal failed - the chart might have been recreated
      }
      
      // Create and add the regression line
      if (pBoundaryData.regression_line?.x?.length > 0) {
        try {
          const regressionSeries = chart.addLineSeries({
            priceScaleId: 'right',
            color: theme.palette.info.main,
            axisLabelVisible: true,
            crosshairMarkerVisible: false,
            lastValueVisible: false,
            lineStyle: LineStyle.Dotted,
            lineType: LineType.Curved,
            lineWidth: 2,
            priceLineVisible: false,
            title: t('Regression'),
            priceFormat: {
              type: 'custom',
              formatter: (price) =>
                `${formatIntlNumber(price, 3, 3)} ${
                  isTether ? t('KRW') : '%'
                }`,
            },
          });
          
          // Set the data for the regression line
          regressionSeries.setData(
            pBoundaryData.regression_line.x.map((date, idx) => ({
              time: DateTime.fromISO(date, { zone: 'UTC' }).toMillis() / 1000,
              value: pBoundaryData.regression_line.y?.[idx],
            }))
          );
          
          // Store the reference to the series
          chartDataRef.current.regressionSeries = regressionSeries;
          
        } catch (error) {
          console.warn('Error creating regression line', error);
        }
      }
      
      // Create and add the prediction points - ensuring they match entry/exit values
      if (pBoundaryData.predicted_points?.y?.length > 0) {
        try {
          const predictionSeries = chart.addCandlestickSeries({
            priceScaleId: 'right',
            borderVisible: false,
            downColor: 'transparent',
            upColor: 'transparent',
            wickDownColor: 'transparent',
            wickUpColor: 'transparent',
            crosshairMarkerVisible: false,
            lastValueVisible: false,
            priceLineVisible: false,
            priceFormat: {
              type: 'custom',
              formatter: (price) =>
                `${formatIntlNumber(price, 3, 3)} ${
                  isTether ? t('KRW') : '%'
                }`,
            },
          });
          
          const [entryDate] = pBoundaryData.predicted_points.x;
          // Use current entry/exit values if available, otherwise use prediction
          const predictedEntry = parsedEntry || pBoundaryData.predicted_points.y[0];
          const predictedExit = parsedExit || pBoundaryData.predicted_points.y[1];
          
          // Set the data for the prediction series
          predictionSeries.setData([
            {
              time: DateTime.fromISO(entryDate, { zone: 'UTC' }).toMillis() / 1000,
              open: predictedEntry,
              close: predictedExit,
              low: predictedEntry,
              high: predictedExit,
            },
          ]);
          
          // Set the markers for the prediction series
          // Use current values for the marker text
          predictionSeries.setMarkers([
            {
              time: DateTime.fromISO(entryDate, { zone: 'UTC' }).toMillis() / 1000,
              position: 'belowBar',
              color: theme.palette.accent.main, // Use same color as entry line
              shape: 'arrowUp',
              text: `${predictedEntry}`,
            },
            {
              time: DateTime.fromISO(entryDate, { zone: 'UTC' }).toMillis() / 1000,
              position: 'aboveBar',
              color: theme.palette.warning.main, // Use same color as exit line
              shape: 'arrowDown',
              text: `${predictedExit}`,
            }
          ]);
          
          // Store the reference to the series
          chartDataRef.current.predictionSeries = predictionSeries;
          
        } catch (error) {
          console.warn('Error creating prediction series', error);
        }
      }
      
      // Notify that we updated triggerConfig
      onTriggerConfigChange({
        entry: parsedEntry,
        exit: parsedExit,
        isTether,
      });
    };

    // Handle successful pBoundary query
    useEffect(() => {
      if (isPBoundarySuccess && pBoundary) {
        // Store the boundary data
        setPBoundaryData(pBoundary);
        
        // Set entry/exit values
        if (pBoundary?.predicted_points?.y?.length > 0) {
          const [predictedEntry, predictedExit] = pBoundary.predicted_points.y;
          setValue('entry', predictedEntry);
          setValue('exit', predictedExit);
          trigger('tradeCapital');
        }
        
        // Apply the visualizations to the chart
        setTimeout(() => {
          applyVisualizationsToChart(true);
        }, 100); // Small delay to ensure chart is ready
      }
    }, [pBoundary, isPBoundarySuccess]);

    // Listen for chart data type or tether changes
    useEffect(() => {
      if (pBoundaryData) {
        // Short delay to ensure chart is updated first
        setTimeout(() => {
          applyVisualizationsToChart();
        }, 200);
      }
    }, [isTether, i18n.language]);

    // Add a listener for chart visibility changes or tab changes
    useEffect(() => {
      const handleVisibilityChange = () => {
        if (document.visibilityState === 'visible' && pBoundaryData) {
          setTimeout(() => {
            applyVisualizationsToChart(true);
          }, 300);
        }
      };
      
      document.addEventListener('visibilitychange', handleVisibilityChange);
      window.addEventListener('focus', handleVisibilityChange);
      
      // Create a MutationObserver to detect chart changes
      const observer = new MutationObserver(() => {
        if (pBoundaryData) {
          setTimeout(() => {
            applyVisualizationsToChart();
          }, 300);
        }
      });
      
      // Find the chart container element and observe changes
      // Use a more reliable selector or wait for the element to be available
      setTimeout(() => {
        const chartContainer = document.querySelector('.tv-lightweight-charts') || 
                              document.querySelector('[data-testid="chart-container"]') ||
                              document.querySelector('.chart-container');
        
        if (chartContainer) {
          observer.observe(chartContainer, { 
            childList: true, 
            subtree: true, 
            attributes: true 
          });
        }
      }, 500); // Give the chart time to render
      
      return () => {
        document.removeEventListener('visibilitychange', handleVisibilityChange);
        window.removeEventListener('focus', handleVisibilityChange);
        observer.disconnect();
      };
    }, [pBoundaryData]);

    // Monitor for chart tab changes
    useEffect(() => {
      // Use a custom event to detect chart type changes
      const chartTypeChangeHandler = () => {
        if (pBoundaryData) {
          setTimeout(() => {
            applyVisualizationsToChart(true);
          }, 300);
        }
      };
      
      document.addEventListener('chartTypeChanged', chartTypeChangeHandler);
      
      return () => {
        document.removeEventListener('chartTypeChanged', chartTypeChangeHandler);
      };
    }, [pBoundaryData]);

    // Add cleanup effect
    useEffect(() => () => {
      // Make sure to clean up any chart series when component unmounts
      const klineChartRef = premiumDataViewerRef?.current?.getKlineChartRef();
      const chart = klineChartRef?.current?.getChart();
      
      if (chart) {
        try {
          if (chartDataRef.current.regressionSeries) {
            chart.removeSeries(chartDataRef.current.regressionSeries);
          }
          if (chartDataRef.current.predictionSeries) {
            chart.removeSeries(chartDataRef.current.predictionSeries);
          }
        } catch (error) {
          console.warn('Error cleaning up chart series', error);
        }
      }
    }, []);

    useEffect(() => {
      autoSetupForm.reset();
      predictionSeriesRef.current?.setData([]);
      regressionLineSeriesRef.current?.setData([]);
      if (setup === 'auto') reset();
    }, [setup]);

    useEffect(() => {
      const target = exchangeApiKey?.find(
        (o) => o.market_code === tradeConfigAllocation?.target_market_code
      );
      const origin = exchangeApiKey?.find(
        (o) => o.market_code === tradeConfigAllocation?.origin_market_code
      );
      if (target && origin) setApiKeys({ target, origin });
    }, [exchangeApiKey, tradeConfigAllocation]);

    useEffect(() => {
      reset();
      autoSetupForm.reset(
        { klineNum: 200, interval, percentGap: 1 }
        // { keepDirtyValues: true }
      );
      predictionSeriesRef.current = null;
      regressionLineSeriesRef.current = null;
    }, [interval]);

    useEffect(() => {
      if (tradeType === 'alarm') setAutoRepeat(0);
    }, [tradeType]);

    useEffect(() => {
      if (disabled) {
        reset();
        autoSetupForm.reset();
        predictionSeriesRef.current?.setData([]);
        regressionLineSeriesRef.current?.setData([]);
      }
    }, [disabled]);

    useEffect(() => () => onTriggerConfigChange({}), []);

    // If we have previously calculated pBoundary data and isTether changes, recalculate
    useEffect(() => {
      if (pBoundary && setup === 'auto' && isSetupValid) {
        const data = autoSetupForm.getValues();
        getPBoundary({
          baseAsset,
          interval,
          marketCodeCombination: `${marketCodes.targetMarketCode}:${marketCodes.originMarketCode}`,
          tradeConfigUuid: tradeConfigAllocation?.trade_config_uuid,
          usdtConversion: isTether,
          ...data,
        });
      }
    }, [isTether]);

    // Add a direct handler for when entry/exit values change to update visualization
    useEffect(() => {
      if (pBoundaryData && (entry || exit)) {
        // This ensures arrows update when entry/exit values change
        setTimeout(() => {
          applyVisualizationsToChart(true);
        }, 100);
      }
    }, [entry, exit]);

    // Add a special effect for handling external isTether changes
    // This will capture changes from the main table's showTether switch
    const prevIsTetherView = usePrevious(isTetherPriceView);
    useEffect(() => {
      // Check if isTetherPriceView changed from external source
      if (prevIsTetherView !== undefined && prevIsTetherView !== isTetherPriceView) {
        // Update our local isTether state
        setValue('isTether', isTetherPriceView);
        
        // If we have boundary data, refresh visualizations
        if (pBoundaryData) {
          setTimeout(() => {
            applyVisualizationsToChart(true);
          }, 200);
        }
        
        // If in auto mode with calculation, recalculate
        if (pBoundary && setup === 'auto' && isSetupValid) {
          const data = autoSetupForm.getValues();
          getPBoundary({
            baseAsset,
            interval,
            marketCodeCombination: `${marketCodes.targetMarketCode}:${marketCodes.originMarketCode}`,
            tradeConfigUuid: tradeConfigAllocation?.trade_config_uuid,
            usdtConversion: isTetherPriceView,
            ...data,
          });
        }
      }
    }, [isTetherPriceView]);

    // 4. Add a "ping" function that we'll call periodically to check for changes
    const pingChart = () => {
      // This function will be called periodically to check if visualizations need to be reapplied
      const klineChartRef = premiumDataViewerRef?.current?.getKlineChartRef();
      const chart = klineChartRef?.current?.getChart();
      
      if (chart && pBoundaryData) {
        // Check if our series are visible in the chart
        let needsRedraw = false;
        
        try {
          // Simple visibility check - if these throw errors, series needs to be redrawn
          if (chartDataRef.current.regressionSeries) {
            const visibility = chartDataRef.current.regressionSeries.options().visible;
            if (visibility === undefined) needsRedraw = true;
          } else if (pBoundaryData?.regression_line?.x?.length > 0) {
            needsRedraw = true;
          }
          
          if (chartDataRef.current.predictionSeries) {
            const visibility = chartDataRef.current.predictionSeries.options().visible;
            if (visibility === undefined) needsRedraw = true;
          } else if (pBoundaryData?.predicted_points?.y?.length > 0) {
            needsRedraw = true;
          }
        } catch (e) {
          // An error means the series is no longer valid - redraw needed
          needsRedraw = true;
        }
        
        if (needsRedraw) {
          applyVisualizationsToChart(true);
        }
        
        return needsRedraw; // Return whether we needed to redraw
      }
      
      return false; // Return false if chart or pBoundaryData doesn't exist
    };

    // 5. Set up a more reliable periodic check for visualization state
    useEffect(() => {
      if (pBoundaryData) {
        // Do initial application
        setTimeout(() => {
          applyVisualizationsToChart(true);
        }, 300);
        
        // Set up periodic checks - rename 'interval' to 'checkInterval' to avoid name conflict
        const checkInterval = setInterval(pingChart, 1000);
        return () => {
          clearInterval(checkInterval);
          return undefined; // Explicit return to satisfy consistent-return rule
        };
      }
      return undefined; // Explicit return when pBoundaryData is falsy
    }, [pBoundaryData]);

    if (isFetching) return <LinearProgress />;

    if (isError || (isSuccess && !apiKeys))
      return (
        <Box
          sx={{
            color: 'error.main',
            fontStyle: 'italic',
            py: 4,
            textAlign: 'center',
          }}
        >
          {t('Invalid API Keys!')}
        </Box>
      );

    return (
      <Box sx={{ py: 4, opacity: disabled ? 0.2 : 1 }}>
        <Box
          id="auto-setup-form"
          component="form"
          autoComplete="off"
          onSubmit={autoSetupForm.handleSubmit(onCalculate)}
          sx={{ px: { md: 4, xs: 2 }, mb: 4 }}
        >
          <Grid container spacing={{ md: 4, xs: 2 }}>
            <Grid item md={2} xs={12}>
              <ToggleButtonGroup
                exclusive
                disabled={disabled}
                value={setup}
                onChange={(e, newSetup) => {
                  e.stopPropagation();
                  if (newSetup !== null) setSetup(newSetup);
                }}
                color="secondary"
                size="small"
              >
                <ToggleButton value="manual" sx={{ px: 2, py: 0.5 }}>
                  {t('Manual')}
                </ToggleButton>
                <ToggleButton value="auto" sx={{ px: 2, py: 0.5 }}>
                  {t('Auto')}
                </ToggleButton>
              </ToggleButtonGroup>
            </Grid>
            {setup === 'auto' && (
              <>
                <Grid
                  item
                  md={4}
                  xs={12}
                  className="animate__animated animate__fadeIn"
                >
                  <Controller
                    name="klineNum"
                    control={autoSetupForm.control}
                    defaultValue={50}
                    rules={{
                      required: true,
                      valueAsNumber: true,
                      validate: {
                        range: (value) =>
                          (value >= 50 && value <= 500) ||
                          t('Value out of range'),
                      },
                    }}
                    render={({ field, fieldState }) => (
                      <FormControl
                        fullWidth
                        error={!!fieldState.error}
                        variant="standard"
                      >
                        <Stack
                          direction="row"
                          alignItems="flex-end"
                          spacing={2}
                          sx={{ mb: 2 }}
                        >
                          <FormLabel>
                            {t('Training Kline')} <small>[50 ~ 500]</small>
                          </FormLabel>
                          <Input
                            inputProps={{
                              min: 50,
                              max: 500,
                              step: 1,
                              type: 'number',
                            }}
                            {...field}
                            value={field.value.toString()}
                            onChange={(e) => {
                              const value = Number(e.target.value);
                              field.onChange(value);
                            }}
                            sx={{ width: '5em' }}
                          />
                          <Typography>개</Typography>
                        </Stack>
                        <Slider
                          // marks
                          min={50}
                          max={500}
                          // step={1}
                          color={fieldState.error ? 'error' : 'info'}
                          valueLabelDisplay="auto"
                          {...field}
                        />
                        <FormHelperText>
                          {fieldState.error?.message}
                        </FormHelperText>
                      </FormControl>
                    )}
                  />
                  <Divider sx={{ my: { md: 2, xs: 0 } }} />
                </Grid>
                <Grid
                  item
                  md={2}
                  xs={12}
                  className="animate__animated animate__fadeIn"
                >
                  <Controller
                    name="percentGap"
                    control={autoSetupForm.control}
                    rules={{ required: true }}
                    render={({ field, fieldState }) => (
                      <FormControl fullWidth error={!!fieldState.error}>
                        <FormLabel sx={{ my: 1 }}>{t('Gap')}</FormLabel>
                        <OutlinedInput
                          disabled={disabled}
                          readOnly={isDollarFetching || isLoading}
                          type="number"
                          size="small"
                          endAdornment={
                            <InputAdornment position="end">%</InputAdornment>
                          }
                          inputProps={{ min: 0, step: 0.05, type: 'number' }}
                          {...field}
                        />
                        <FormHelperText>
                          {fieldState.error?.message}
                        </FormHelperText>
                      </FormControl>
                    )}
                  />
                </Grid>
                <Grid
                  item
                  md={4}
                  xs={12}
                  alignSelf="center"
                  className="animate__animated animate__fadeIn"
                >
                  <Button
                    disabled={
                      !isSetupValid ||
                      isLoading ||
                      disabled ||
                      isPBoundaryFetching
                    }
                    form="auto-setup-form"
                    type="submit"
                    variant="contained"
                  >
                    {t('Calculate')}
                  </Button>
                </Grid>
              </>
            )}
          </Grid>
        </Box>
        <Box
          id="create-trigger-form"
          component="form"
          autoComplete="off"
          onSubmit={handleSubmit(onSubmit)}
          sx={{ px: { md: 4, xs: 2 } }}
        >
          <Grid container spacing={3}>
            {showTether && (
              <Grid item md={2} xs={12}>
                <Controller
                  name="isTether"
                  control={control}
                  render={({ field }) => (
                    <FormControlLabel
                      control={<Checkbox />}
                      disabled={isDollarFetching || isLoading || disabled}
                      label={t('USDT Conversion')}
                      checked={!!field.value}
                      sx={{
                        alignItems: 'flex-end',
                        span: { paddingBottom: 0 },
                      }}
                      {...field}
                      onChange={(event) => {
                        field.onChange(event);
                        
                        // If we have setup values, recalculate with new tether value
                        if (isSetupValid && setupSubmitCount > 0) {
                          const data = autoSetupForm.getValues();
                          getPBoundary({
                            baseAsset,
                            interval,
                            marketCodeCombination: `${marketCodes.targetMarketCode}:${marketCodes.originMarketCode}`,
                            tradeConfigUuid: tradeConfigAllocation?.trade_config_uuid,
                            usdtConversion: event.target.checked,
                            ...data,
                          });
                        } 
                        // Otherwise if we have existing pBoundary data, reapply visualizations
                        else if (pBoundaryData) {
                          // When toggling tether mode, we may need to convert entry/exit values
                          if (dollar?.price && isDollarSuccess) {
                            try {
                              const entryValue = getValues('entry');
                              const exitValue = getValues('exit');
                              
                              if (entryValue) {
                                const parsedEntry = parseFloat(entryValue);
                                if (event.target.checked && parsedEntry <= 500) {
                                  // Converting % to KRW
                                  setValue(
                                    'entry',
                                    (dollar.price * (1 + parsedEntry / 100)).toFixed(3)
                                  );
                                } else if (!event.target.checked && parsedEntry > 500) {
                                  // Converting KRW to %
                                  setValue(
                                    'entry',
                                    (100 * (parsedEntry / dollar.price - 1)).toFixed(3)
                                  );
                                }
                              }
                              
                              if (exitValue) {
                                const parsedExit = parseFloat(exitValue);
                                if (event.target.checked && parsedExit <= 500) {
                                  // Converting % to KRW
                                  setValue(
                                    'exit',
                                    (dollar.price * (1 + parsedExit / 100)).toFixed(3)
                                  );
                                } else if (!event.target.checked && parsedExit > 500) {
                                  // Converting KRW to %
                                  setValue(
                                    'exit',
                                    (100 * (parsedExit / dollar.price - 1)).toFixed(3)
                                  );
                                }
                              }
                            } catch (e) {
                              console.warn('Error converting entry/exit values', e);
                            }
                          }
                          
                          setTimeout(() => {
                            applyVisualizationsToChart(true);
                          }, 200);
                        }
                      }}
                    />
                  )}
                />
              </Grid>
            )}
            {setup === 'auto' && tradeType === 'autoTrade' && (
              <Grid
                item
                md
                xs={12}
                className="animate__animated animate__fadeIn"
              >
                <Stack alignItems="center" direction="row" spacing={2}>
                  <FormControlLabel
                    checked={!!autoRepeat}
                    onChange={(e) => setAutoRepeat(e.target.checked ? 1 : 0)}
                    control={<Switch color="primary" />}
                    label={t('Auto Repeat')}
                    labelPlacement="start"
                  />
                </Stack>
              </Grid>
            )}
            <Grid item md xs={12} sx={{ pt: '12px !important' }}>
              <Controller
                name="entry"
                control={control}
                rules={{
                  required: true,
                  validate: {
                    lessThanExit: (value) => {
                      const exitValue = getValues('exit');
                      if (
                        exitValue &&
                        parseFloat(value) >= parseFloat(exitValue)
                      )
                        return t('Entry must be lower than exit');
                      return true;
                    },
                  },
                }}
                render={({ field, fieldState }) => (
                  <FormControl
                    fullWidth
                    error={!!fieldState.error}
                    variant="standard"
                  >
                    <InputLabel>{t('Entry')}</InputLabel>
                    <Input
                      disabled={disabled}
                      readOnly={
                        isDollarFetching || isLoading || setup === 'auto'
                      }
                      type="number"
                      startAdornment={
                        <InputAdornment position="start">
                          <TrendingDownIcon
                            color={entry ? 'accent' : undefined}
                            fontSize="small"
                          />
                        </InputAdornment>
                      }
                      endAdornment={
                        <InputAdornment position="end">
                          {isTether ? t('KRW') : '%'}
                        </InputAdornment>
                      }
                      inputProps={{ precision: 2, step: 0.1 }}
                      {...field}
                      onChange={(e) => {
                        const { value } = e.target;
                        if (value && !isTether && parseFloat(value) > 500)
                          return;
                        field.onChange(e);
                      }}
                    />
                    <FormHelperText>{fieldState.error?.message}</FormHelperText>
                  </FormControl>
                )}
              />
            </Grid>
            <Grid item md xs={12} sx={{ pt: '12px !important' }}>
              <Controller
                name="exit"
                control={control}
                rules={{
                  required: true,
                  validate: {
                    greaterThanEntry: (value) => {
                      const entryValue = getValues('entry');
                      if (
                        entryValue &&
                        parseFloat(value) <= parseFloat(entryValue)
                      )
                        return t('Exit must be higher than entry');
                      return true;
                    },
                  },
                }}
                render={({ field, fieldState }) => (
                  <FormControl
                    fullWidth
                    error={!!fieldState.error}
                    variant="standard"
                  >
                    <InputLabel>{t('Exit')}</InputLabel>
                    <Input
                      disabled={disabled}
                      readOnly={
                        isDollarFetching || isLoading || setup === 'auto'
                      }
                      type="number"
                      startAdornment={
                        <InputAdornment position="start">
                          <TrendingUpIcon
                            color={exit ? 'warning' : undefined}
                            fontSize="small"
                          />
                        </InputAdornment>
                      }
                      endAdornment={
                        <InputAdornment position="end">
                          {isTether ? t('KRW') : '%'}
                        </InputAdornment>
                      }
                      inputProps={{ step: 0.1 }}
                      {...field}
                      onChange={(e) => {
                        const { value } = e.target;
                        if (value && !isTether && parseFloat(value) > 500)
                          return;
                        field.onChange(e);
                      }}
                    />
                    <FormHelperText>{fieldState.error?.message}</FormHelperText>
                  </FormControl>
                )}
              />
            </Grid>
            {tradeType === 'autoTrade' && (
              <Grid item md xs={12} sx={{ pt: '12px !important' }}>
                <Controller
                  name="tradeCapital"
                  control={control}
                  defaultValue=""
                  rules={{
                    required: true,
                    validate: {
                      minimum: (value) =>
                        parseInt(value?.replace(/,/g, ''), 10) >= 10000 ||
                        t('Trade capital must be at least 10,000 or more.'),
                    },
                  }}
                  render={({ field, fieldState }) => (
                    <NumberFormatWrapper
                      fullWidth
                      thousandSeparator
                      allowNegative={false}
                      decimalScale={0}
                      customInput={TextField}
                      error={!!fieldState.error}
                      label={t('Trade Capital')}
                      variant="standard"
                      InputProps={{
                        startAdornment: (
                          <InputAdornment position="start">
                            <PaymentIcon fontSize="small" />
                          </InputAdornment>
                        ),
                        endAdornment: (
                          <InputAdornment position="end">
                            {t('KRW')}
                          </InputAdornment>
                        ),
                      }}
                      {...field}
                    />
                  )}
                />
              </Grid>
            )}
            <Grid item md xs={12}>
              <Stack direction="row" spacing={1}>
                <Button
                  fullWidth
                  form="create-trigger-form"
                  type="submit"
                  variant="contained"
                  disabled={
                    !isValid ||
                    isLoading ||
                    disabled ||
                    (setup === 'auto' && !isSetupValid)
                  }
                  endIcon={
                    isLoading ? (
                      <CircularProgress color="inherit" size={15} />
                    ) : (
                      <ArrowForwardIcon />
                    )
                  }
                >
                  {t('Register')}
                </Button>
                <Button disabled={!isDirty || disabled} onClick={() => reset()}>
                  {t('Clear')}
                </Button>
              </Stack>
            </Grid>
          </Grid>
          <Box sx={{ position: 'relative', mt: 4 }}>
            <Snackbar
              open={!!alertMessage}
              autoHideDuration={2000}
              onClose={() => setAlertMessage(null)}
              anchorOrigin={{ horizontal: 'center', vertical: 'bottom' }}
              sx={{ position: 'absolute' }}
            >
              <Alert
                severity={alertMessage?.status}
                onClose={() => setAlertMessage(null)}
              >
                {alertMessage?.message}
              </Alert>
            </Snackbar>
          </Box>
        </Box>
      </Box>
    );
  }
);

export default React.memo(CreateTriggerForm);
