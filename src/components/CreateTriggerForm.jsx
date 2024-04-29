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
import OutlinedInput from '@mui/material/OutlinedInput';
import Slider from '@mui/material/Slider';
import Snackbar from '@mui/material/Snackbar';
import Stack from '@mui/material/Stack';
import Switch from '@mui/material/Switch';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Typography from '@mui/material/Typography';

import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';

import { useTheme } from '@mui/material/styles';

import { LineStyle, LineType } from 'lightweight-charts';

import { Controller, useForm, useWatch } from 'react-hook-form';

import { useTranslation } from 'react-i18next';

import { useSelector } from 'react-redux';

import { useGetDollarQuery } from 'redux/api/drf/infocore';
import {
  useLazyGetPBoundaryQuery,
  usePostRepeatTradeMutation,
  usePostTradeMutation,
  usePostTradeConfigMutation,
} from 'redux/api/drf/tradecore';

import { DateTime } from 'luxon';

import { usePrevious } from '@uidotdev/usehooks';

import isKoreanMarket from 'utils/isKoreanMarket';

const CreateTriggerForm = forwardRef(
  (
    {
      baseAsset,
      marketCodes,
      interval,
      isTetherPriceView,
      tradeConfigAllocation,
      onTriggerConfigChange,
      onCreateSuccess,
      premiumDataViewerRef,
    },
    ref
  ) => {
    const regressionLineSeriesRef = useRef();

    const { t } = useTranslation();

    const theme = useTheme();

    const user = useSelector((state) => state.auth.user);

    const [alertMessage, setAlertMessage] = useState(null);
    const [autoRepeat, setAutoRepeat] = useState(0);
    const [disabled, setDisabled] = useState(false);
    const [setup, setSetup] = useState('manual');

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
      defaultValues: { klineNum: 50, interval: '1T', percentGap: '' },
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
        gap: '',
        trainingKline: 50,
        isTether: isTetherPriceView || false,
      },
      mode: 'all',
    });

    const { isDirty, isValid } = formState;

    const entry = useWatch({ control, name: 'entry' });
    const exit = useWatch({ control, name: 'exit' });
    const isTether = useWatch({ control, name: 'isTether' });

    const {
      data: dollar,
      isFetching: isDollarFetching,
      isSuccess: isDollarSuccess,
    } = useGetDollarQuery({}, { skip: !isTether });

    const [postRepeatTrade] = usePostRepeatTradeMutation();
    const [postTrade, tradeResults] = usePostTradeMutation();
    const [postTradeConfig, tradeConfigResults] = usePostTradeConfigMutation();

    const [getPBoundary, pBoundary] = useLazyGetPBoundaryQuery();

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

      let trade;
      let tradeConfigUuid = tradeConfigAllocation?.trade_config_uuid;
      if (isValid)
        if (!tradeConfigAllocation) {
          try {
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
            }).unwrap();
          } catch (err) {
            setAlertMessage({
              message: t('An error occurred. Please try again.'),
              status: 'error',
            });
          }
        } else
          trade = await postTrade({
            base_asset: baseAsset,
            trade_config_uuid: tradeConfigAllocation.trade_config_uuid,
            usdt_conversion: data.isTether,
            low: parseFloat(data.entry),
            high: parseFloat(data.exit),
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

    useEffect(() => {
      const klineChartRef = premiumDataViewerRef?.current?.getKlineChartRef();
      if (pBoundary.data?.regression_line?.x?.length > 0) {
        if (!regressionLineSeriesRef.current)
          regressionLineSeriesRef.current = klineChartRef?.current
            ?.getChart()
            ?.addLineSeries({
              priceScaleId: 'right',
              color: theme.palette.success.light,
              crosshairMarkerVisible: false,
              lastValueVisible: false,
              lineStyle: LineStyle.Dashed,
              lineType: LineType.Curved,
              lineWidth: 3,
              // pointMarkersRadius: 3,
              // pointMarkersVisible: true,
              priceLineVisible: false,
            });
        regressionLineSeriesRef.current?.setData(
          pBoundary.data.regression_line.x.map((date, idx) => ({
            time:
              DateTime.fromISO(date, {
                zone: 'UTC',
              }).toMillis() / 1000,
            value: pBoundary.data.regression_line.y?.[idx],
          }))
        );
      }
      if (pBoundary.data?.predicted_points?.y?.length > 0) {
        const [predictedEntry, predictedExit] =
          pBoundary.data.predicted_points.y;
        setValue('entry', predictedEntry);
        setValue('exit', predictedExit);
        klineChartRef?.current?.getCandlestickSeries()?.setMarkers(
          pBoundary.data.predicted_points.x.map((date, idx) => ({
            time:
              DateTime.fromISO(date, {
                zone: 'UTC',
              }).toMillis() / 1000,
            position: idx === 0 ? 'belowBar' : 'aboveBar',
            color: theme.palette.error.light,
            shape: idx === 0 ? 'arrowUp' : 'arrowDown',
            text: `${pBoundary.data.predicted_points.y?.[idx]}`,
          }))
        );
      }
    }, [pBoundary]);

    const prevIsTether = usePrevious(isTether);
    useEffect(() => {
      if (setup === 'manual') {
        if (prevIsTether && !isTether) {
          const entryValue = getValues('entry');
          if (entryValue && parseFloat(entryValue) > 500)
            setValue(
              'entry',
              (100 * (parseFloat(entryValue) / dollar.price - 1)).toFixed(3)
            );
          const exitValue = getValues('exit');
          if (exitValue && parseFloat(exitValue) > 500)
            setValue(
              'exit',
              (100 * (parseFloat(exitValue) / dollar.price - 1)).toFixed(3)
            );
        }
      }
    }, [isTether, setup]);

    useEffect(() => {
      autoSetupForm.reset();
      regressionLineSeriesRef.current?.setData([]);
      premiumDataViewerRef?.current
        ?.getKlineChartRef()
        ?.current?.getCandlestickSeries()
        ?.setMarkers([]);
      if (setup === 'auto') {
        reset();
      }
    }, [setup]);

    useEffect(() => {
      if (disabled) {
        reset();
        autoSetupForm.reset();
        regressionLineSeriesRef.current?.setData([]);
      }
    }, [disabled]);

    useEffect(() => () => onTriggerConfigChange({}), []);

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
                          inputProps={{ min: 0, step: 'any', type: 'number' }}
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
                      pBoundary.isFetching
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
                      onChange={(e) => {
                        field.onChange(e);
                        if (isSetupValid && setupSubmitCount > 0) {
                          const data = autoSetupForm.getValues();
                          getPBoundary({
                            baseAsset,
                            interval,
                            marketCodeCombination: `${marketCodes.targetMarketCode}:${marketCodes.originMarketCode}`,
                            tradeConfigUuid:
                              tradeConfigAllocation.trade_config_uuid,
                            usdtConversion: e.target.checked,
                            ...data,
                          });
                        }
                      }}
                    />
                  )}
                />
              </Grid>
            )}
            {setup === 'auto' && (
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
