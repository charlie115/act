import React, {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useMemo,
  useState,
} from 'react';

import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Checkbox from '@mui/material/Checkbox';
import CircularProgress from '@mui/material/CircularProgress';
import FormControl from '@mui/material/FormControl';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormHelperText from '@mui/material/FormHelperText';
import Grid from '@mui/material/Grid';
import Input from '@mui/material/Input';
import InputAdornment from '@mui/material/InputAdornment';
import InputLabel from '@mui/material/InputLabel';
import Snackbar from '@mui/material/Snackbar';
import Stack from '@mui/material/Stack';

import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';

import { Controller, useForm, useWatch } from 'react-hook-form';

import { useTranslation } from 'react-i18next';

import { useSelector } from 'react-redux';

import { useGetDollarQuery } from 'redux/api/drf/infocore';
import {
  usePostTradeMutation,
  usePostTradeConfigMutation,
} from 'redux/api/drf/tradecore';

import { usePrevious } from '@uidotdev/usehooks';

import isKoreanMarket from 'utils/isKoreanMarket';

const CreateAlarmForm = forwardRef(
  (
    {
      baseAsset,
      marketCodes,
      isTetherPriceView,
      tradeConfigAllocation,
      onAlarmConfigChange,
    },
    ref
  ) => {
    const { t } = useTranslation();

    const user = useSelector((state) => state.auth.user);

    const [alertMessage, setAlertMessage] = useState(null);
    const [disabled, setDisabled] = useState(false);

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

    const {
      control,
      handleSubmit,
      formState,
      getValues,
      reset,
      setValue,
      trigger,
    } = useForm({
      defaultValues: {
        entry: '',
        exit: '',
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

    const [postTrade, tradeResults] = usePostTradeMutation();
    const [postTradeConfig, tradeConfigResults] = usePostTradeConfigMutation();

    const isLoading = tradeResults.isLoading || tradeConfigResults.isLoading;

    const onSubmit = async (data) => {
      if (isValid)
        if (!tradeConfigAllocation) {
          try {
            const results = await postTradeConfig({
              acw_user_uuid: user?.uuid,
              target_market_code: marketCodes?.targetMarketCode,
              origin_market_code: marketCodes?.originMarketCode,
            }).unwrap();
            postTrade({
              base_asset: baseAsset,
              trade_config_uuid: results.uuid,
              usdt_conversion: data.isTether,
              low: parseFloat(data.entry),
              high: parseFloat(data.exit),
            });
          } catch (err) {
            setAlertMessage({
              message: t('An error occurred. Please try again.'),
              status: 'error',
            });
          }
        } else
          postTrade({
            base_asset: baseAsset,
            trade_config_uuid: tradeConfigAllocation.trade_config_uuid,
            usdt_conversion: data.isTether,
            low: parseFloat(data.entry),
            high: parseFloat(data.exit),
          });
    };

    useEffect(() => {
      if (tradeResults.isSuccess) {
        reset();
        setAlertMessage({
          message: t('Successfully registered alarm.'),
          status: 'success',
        });
      } else if (tradeResults.isError) {
        setAlertMessage({
          message: t('An error occurred. Please try again.'),
          status: 'error',
        });
      }
    }, [tradeResults.isError, tradeResults.isSuccess]);

    useEffect(() => {
      if (entry && exit) trigger(['entry', 'exit']);
      onAlarmConfigChange({
        entry: entry ? parseFloat(entry) : null,
        exit: exit ? parseFloat(exit) : null,
        isTether,
      });
    }, [entry, exit, isTether]);

    useEffect(() => {
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
    }, [dollar, isDollarSuccess]);

    const prevIsTether = usePrevious(isTether);
    useEffect(() => {
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
    }, [isTether]);

    useEffect(() => {
      if (disabled) reset();
    }, [disabled]);

    useEffect(() => () => onAlarmConfigChange({}), []);

    return (
      <Box
        id="create-alarm-form"
        component="form"
        autoComplete="off"
        onSubmit={handleSubmit(onSubmit)}
        sx={{ mt: 6, opacity: disabled ? 0.2 : 1 }}
      >
        <Grid container spacing={3} sx={{ px: { xs: 2, md: 4 } }}>
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
                  />
                )}
              />
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
                    if (exitValue && parseFloat(value) >= parseFloat(exitValue))
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
                    readOnly={isDollarFetching || isLoading}
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
                      if (value && !isTether && parseFloat(value) > 500) return;
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
                    readOnly={isDollarFetching || isLoading}
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
                      if (value && !isTether && parseFloat(value) > 500) return;
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
                type="submit"
                variant="contained"
                disabled={!isValid || isLoading || disabled}
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
    );
  }
);

export default React.memo(CreateAlarmForm);
