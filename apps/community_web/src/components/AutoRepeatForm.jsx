import React, { useEffect } from 'react';

import Box from '@mui/material/Box';
import FormControl from '@mui/material/FormControl';
import FormHelperText from '@mui/material/FormHelperText';
import FormLabel from '@mui/material/FormLabel';
import Input from '@mui/material/Input';
import InputAdornment from '@mui/material/InputAdornment';
import LinearProgress from '@mui/material/LinearProgress';
import OutlinedInput from '@mui/material/OutlinedInput';
import Slider from '@mui/material/Slider';
import Stack from '@mui/material/Stack';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Typography from '@mui/material/Typography';

import { Controller, useForm, useWatch } from 'react-hook-form';

import { useTranslation } from 'react-i18next';

import {
  useLazyGetRepeatTradesByTradeConfigQuery,
  useLazyGetTradeLogByUuidQuery,
  usePostRepeatTradeMutation,
  usePutRepeatTradeMutation,
} from 'redux/api/drf/tradecore';

import castString from 'utils/castString';

export default function AutoRepeatForm({
  tradeConfigUuid,
  tradeUuid,
  onSuccess,
}) {
  const { t } = useTranslation();

  const [getRepeatTrades, repeatTradesResult] =
    useLazyGetRepeatTradesByTradeConfigQuery();
  
  const [getTradeLog, tradeLogResult] = useLazyGetTradeLogByUuidQuery();

  const [postRepeatTrade, postResult] = usePostRepeatTradeMutation();
  const [putRepeatTrade, putResult] = usePutRepeatTradeMutation();

  const { control, formState, handleSubmit, reset, setValue, watch } = useForm({
    defaultValues: async () => {
      try {
        const [data] = await getRepeatTrades({
          trade_config_uuid: tradeConfigUuid,
          trade_uuid: tradeUuid,
        }).unwrap();

        return {
          isFixed: `${data?.pauto_num === null}`,
          kline_num: data?.kline_num || 200,
          pauto_num: data?.pauto_num || 1,
          uuid: data?.uuid,
          auto_repeat_num: data?.auto_repeat_num,
          trade_uuid: tradeUuid,
        };
      } catch (error) {
        return {
          isFixed: 'false',
          kline_num: 200,
          pauto_num: 1,
          uuid: null,
          auto_repeat_num: 0,
          trade_uuid: tradeUuid,
        };
      }
    },
    mode: 'all',
  });

  const { isValid } = formState;

  const isFixed = useWatch({ control, name: 'isFixed' });

  useEffect(() => {
    if (castString(isFixed)) {
      getTradeLog({ tradeConfigUuid, uuid: tradeUuid });
    }
  }, [isFixed, tradeUuid, getTradeLog]);

  const onSubmit = (data) => {
    if (!isValid) return;
    
    const isFixedValue = castString(data.isFixed);
    
    if (data.uuid) {
      const payload = {
        auto_repeat_switch: 1,
        auto_repeat_num: data.auto_repeat_num,
        uuid: data.uuid,
        trade_config_uuid: tradeConfigUuid,
        trade_uuid: data.trade_uuid,
      };
      
      if (!isFixedValue) {
        payload.kline_num = data.kline_num;
        payload.pauto_num = data.pauto_num;
      }
      
      putRepeatTrade(payload);
    } else {
      const payload = {
        trade_config_uuid: tradeConfigUuid,
        trade_uuid: tradeUuid,
        auto_repeat_num: 0,
        auto_repeat_switch: 1,
      };
      
      if (!isFixedValue) {
        payload.kline_num = data.kline_num;
        payload.pauto_num = data.pauto_num;
      }
      
      postRepeatTrade(payload);
    }
  };

  useEffect(() => {
    if (putResult.isSuccess) {
      reset();
      if (onSuccess) onSuccess();
    }
  }, [putResult.isSuccess]);

  useEffect(() => {
    if (postResult.isSuccess) {
      reset();
      if (onSuccess) onSuccess();
    }
  }, [postResult.isSuccess]);

  if (repeatTradesResult?.isFetching) return <LinearProgress />;
  if (castString(isFixed) && tradeLogResult?.isFetching) return <LinearProgress />;

  const tradeLogData = tradeLogResult.data;

  return (
    <Box
      id="auto-repeat-form"
      component="form"
      autoComplete="off"
      onSubmit={handleSubmit(onSubmit)}
    >
      <Controller
        name="isFixed"
        control={control}
        render={({ field }) => (
          <ToggleButtonGroup
            {...field}
            exclusive
            onChange={(_, value) => {
              if (value !== null) setValue(field.name, value);
            }}
            color="secondary"
            size="small"
          >
            <ToggleButton
              value="true"
              sx={{ px: 2, py: 0.5 }}
            >
              {t('Fixed')}
            </ToggleButton>
            <ToggleButton value="false" sx={{ px: 2, py: 0.5 }}>
              {t('Re-calculating')}
            </ToggleButton>
          </ToggleButtonGroup>
        )}
      />
      {castString(isFixed) && tradeLogData && (
        <Stack
          spacing={2}
          sx={{ p: 3 }}
          className="animate__animated animate__fadeIn"
        >
          <Stack
            direction="row"
            spacing={2}
            alignItems="center"
          >
            <FormControl sx={{ flex: 1 }} variant="standard">
              <FormLabel sx={{ mb: 1 }}>{t('Entry')}</FormLabel>
              <OutlinedInput
                disabled
                size="small"
                value={tradeLogData.low || "-"}
              />
            </FormControl>
            <FormControl sx={{ flex: 1 }} variant="standard">
              <FormLabel sx={{ mb: 1 }}>{t('Exit')}</FormLabel>
              <OutlinedInput
                disabled
                size="small"
                value={tradeLogData.high || "-"}
              />
            </FormControl>
          </Stack>
        </Stack>
      )}
      {!castString(isFixed) && (
        <Stack
          spacing={2}
          sx={{ p: 3 }}
          className="animate__animated animate__fadeIn"
        >
          <Controller
            name="kline_num"
            control={control}
            defaultValue={50}
            rules={{
              required: true,
              valueAsNumber: true,
              validate: {
                range: (value) =>
                  (value >= 50 && value <= 500) || t('Value out of range'),
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
                    onChange={(e) => {
                      const value = Number(e.target.value);
                      field.onChange(value);
                    }}
                    sx={{ width: '5em' }}
                  />
                  <Typography>개</Typography>
                </Stack>
                <Slider
                  min={50}
                  max={500}
                  color={fieldState.error ? 'error' : 'info'}
                  valueLabelDisplay="auto"
                  {...field}
                />
                <FormHelperText>{fieldState.error?.message}</FormHelperText>
              </FormControl>
            )}
          />
          <Controller
            name="pauto_num"
            control={control}
            defaultValue=""
            rules={{ required: true }}
            render={({ field, fieldState }) => (
              <FormControl fullWidth error={!!fieldState.error}>
                <FormLabel sx={{ my: 1 }}>{t('Gap')}</FormLabel>
                <OutlinedInput
                  type="number"
                  size="small"
                  slotProps={{
                    input: {
                      endAdornment: (
                        <InputAdornment position="end">%</InputAdornment>
                      ),
                    },
                  }}
                  inputProps={{ min: 0, step: 0.05, type: 'number' }}
                  {...field}
                />
                <FormHelperText>{fieldState.error?.message}</FormHelperText>
              </FormControl>
            )}
          />
        </Stack>
      )}
    </Box>
  );
}
