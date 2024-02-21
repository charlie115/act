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

import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';

import { Controller, useForm, useWatch } from 'react-hook-form';

import { useTranslation } from 'react-i18next';

import { usePutTradeMutation } from 'redux/api/drf/tradecore';

export default function UpdateAlarmForm({
  row: { isTether, ...row },
  onAlarmConfigChange,
  toggleExpanded,
}) {
  const { t } = useTranslation();

  const { control, handleSubmit, formState, getValues, trigger } = useForm({
    defaultValues: { entry: row.entry, exit: row.exit },
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
        base_asset: row.base_asset,
        trade_config_uuid: row.trade_config_uuid,
        usdt_conversion: row.usdt_conversion,
        uuid: row.uuid,
      });
  };

  useEffect(() => {
    if (isSuccess) toggleExpanded(false);
  }, [isSuccess]);

  useEffect(() => {
    if (entry && exit) trigger(['entry', 'exit']);
    onAlarmConfigChange({
      entry: entry ? parseFloat(entry) : null,
      exit: exit ? parseFloat(exit) : null,
      isTether,
    });
  }, [entry, exit]);

  useEffect(() => {
    onAlarmConfigChange({
      entry: row.entry || null,
      exit: row.exit || null,
      isTether,
    });
    return () => onAlarmConfigChange({});
  }, []);

  return (
    <Box
      id="update-alarm-form"
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
