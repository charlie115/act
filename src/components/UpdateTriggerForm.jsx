import React, { useEffect } from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import FormControl from '@mui/material/FormControl';
import FormHelperText from '@mui/material/FormHelperText';
import Grid from '@mui/material/Grid';
import Input from '@mui/material/Input';
import InputAdornment from '@mui/material/InputAdornment';
import InputLabel from '@mui/material/InputLabel';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';

import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import PaymentIcon from '@mui/icons-material/Payment';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';

import { Controller, useForm, useWatch } from 'react-hook-form';

import { useTranslation } from 'react-i18next';

import { usePutTradeMutation } from 'redux/api/drf/tradecore';

import NumberFormatWrapper from 'components/NumberFormatWrapper';

export default function UpdateTriggerForm({
  baseAsset,
  defaultEntry,
  defaultExit,
  defaultTradeCapital,
  isTether,
  tradeConfigUuid,
  tradeType,
  usdtConversion,
  uuid,
  onTriggerConfigChange,
  toggleExpanded,
}) {
  const { t } = useTranslation();

  const { control, handleSubmit, formState, getValues, trigger } = useForm({
    defaultValues: {
      entry: defaultEntry,
      exit: defaultExit,
      tradeCapital: tradeType === 'autoTrade' ? defaultTradeCapital : undefined,
    },
    mode: 'all',
  });

  const { isValid } = formState;

  const entry = useWatch({ control, name: 'entry' });
  const exit = useWatch({ control, name: 'exit' });

  const [putTrade, { isLoading, isSuccess }] = usePutTradeMutation();

  const onSubmit = (data) => {
    if (isValid)
      putTrade({
        low: parseFloat(data.entry),
        high: parseFloat(data.exit),
        trade_capital:
          tradeType === 'autoTrade' && !!data.tradeCapital
            ? parseInt(`${data.tradeCapital}`.replace(/,/g, ''), 10)
            : undefined,
        base_asset: baseAsset,
        trade_config_uuid: tradeConfigUuid,
        usdt_conversion: usdtConversion,
        uuid,
      });
  };

  useEffect(() => {
    if (isSuccess) toggleExpanded(false);
  }, [isSuccess]);

  useEffect(() => {
    if (entry && exit) trigger(['entry', 'exit']);
    onTriggerConfigChange({
      entry: entry ? parseFloat(entry) : null,
      exit: exit ? parseFloat(exit) : null,
      isTether,
    });
  }, [entry, exit]);

  useEffect(() => {
    onTriggerConfigChange({
      entry: defaultEntry || null,
      exit: defaultExit || null,
      isTether,
    });
    return () => onTriggerConfigChange({});
  }, []);

  return (
    <Box
      id="update-trigger-form"
      component="form"
      autoComplete="off"
      onSubmit={handleSubmit(onSubmit)}
      sx={{ p: 4 }}
    >
      <Grid container spacing={3} sx={{ px: { xs: 2, md: 4 } }}>
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
                  autoFocus
                  readOnly={isLoading}
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
                  if (entryValue && parseFloat(value) <= parseFloat(entryValue))
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
                  readOnly={isLoading}
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
        {tradeType === 'autoTrade' && (
          <Grid item md xs={12} sx={{ pt: '12px !important' }}>
            <Controller
              name="tradeCapital"
              control={control}
              rules={{ required: true }}
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
                      <InputAdornment position="end">{t('KRW')}</InputAdornment>
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
              type="submit"
              variant="contained"
              disabled={!isValid || isLoading}
              endIcon={
                isLoading ? (
                  <CircularProgress color="inherit" size={15} />
                ) : (
                  <ArrowForwardIcon />
                )
              }
            >
              {t('Update')}
            </Button>
            <Button onClick={() => toggleExpanded(false)}>{t('Cancel')}</Button>
          </Stack>
        </Grid>
      </Grid>
    </Box>
  );
}
