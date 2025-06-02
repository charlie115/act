import React from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import FormControl from '@mui/material/FormControl';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormHelperText from '@mui/material/FormHelperText';
import FormLabel from '@mui/material/FormLabel';
import Input from '@mui/material/Input';
import LinearProgress from '@mui/material/LinearProgress';
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import Slider from '@mui/material/Slider';
import Stack from '@mui/material/Stack';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';

import ArrowForwardIcon from '@mui/icons-material/ArrowForward';

import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

import { useTranslation } from 'react-i18next';

import { Controller, useForm } from 'react-hook-form';

import {
  useLazyGetTradeConfigQuery,
  usePutTradeConfigMutation,
} from 'redux/api/drf/tradecore';

import castString from 'utils/castString';

export default function TradeSupportBotSettings({ marketCodeCombination }) {
  const { t } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const [putTradeConfig, { isLoading: isPutTradeConfigLoading }] =
    usePutTradeConfigMutation();
  const [getTradeConfig] = useLazyGetTradeConfigQuery();

  const { control, formState, handleSubmit } = useForm({
    defaultValues: async () => {
      const data = await getTradeConfig({
        uuid: marketCodeCombination?.tradeConfigUuid,
      }).unwrap();

      const defaultValues = {
        ...data,
        repeat_limit_p: data?.repeat_limit_p || 0,
        safe_reverse: `${!!data?.safe_reverse}`,
        send_term: data?.send_term || 0,
        send_times: data?.send_times || 0,
      };

      if (!marketCodeCombination?.target.isSpot) {
        defaultValues.target_market_cross = `${!!data?.target_market_cross}`;
        defaultValues.target_market_margin_call = `${data?.target_market_margin_call}`;
        defaultValues.target_market_leverage =
          data?.target_market_leverage || 1;
      }

      if (!marketCodeCombination?.origin.isSpot) {
        defaultValues.origin_market_cross = `${!!data?.origin_market_cross}`;
        defaultValues.origin_market_margin_call = `${data?.origin_market_margin_call}`;
        defaultValues.origin_market_leverage =
          data?.origin_market_leverage || 1;
      }
      return defaultValues;
    },
    mode: 'all',
  });

  const { dirtyFields, isDirty, isValid } = formState;

  const onSubmit = (data) => {
    const formData = {
      uuid: data.uuid,
      acw_user_uuid: data.acw_user_uuid,
      target_market_code: data.target_market_code,
      origin_market_code: data.origin_market_code,
    };
    Object.entries(dirtyFields).forEach(([key, value]) => {
      if (value) formData[key] = castString(data[key]);
    });
    putTradeConfig(formData);
  };

  const renderMarginMode = (name) => (
    <Controller
      name={name}
      control={control}
      defaultValue=""
      rules={{ required: true }}
      render={({ field, fieldState }) => (
        <FormControl fullWidth error={!!fieldState.error} variant="standard">
          <RadioGroup row {...field}>
            <FormControlLabel
              value="false"
              control={<Radio size={isMobile ? 'small' : 'medium'} />}
              label={t('Isolated')}
              sx={{ '& .MuiFormControlLabel-label': { fontSize: isMobile ? '0.875rem' : '1rem' } }}
            />
            <FormControlLabel
              value="true"
              control={<Radio size={isMobile ? 'small' : 'medium'} />}
              label={t('Cross')}
              sx={{ '& .MuiFormControlLabel-label': { fontSize: isMobile ? '0.875rem' : '1rem' } }}
            />
          </RadioGroup>
        </FormControl>
      )}
    />
  );

  const renderLiquidationDetection = (name) => (
    <Controller
      name={name}
      control={control}
      defaultValue=""
      rules={{ required: true }}
      render={({ field, fieldState }) => (
        <FormControl fullWidth error={!!fieldState.error} variant="standard">
          <RadioGroup row {...field}>
            <FormControlLabel
              value="null"
              control={<Radio size={isMobile ? 'small' : 'medium'} />}
              label={t('Off')}
              sx={{ '& .MuiFormControlLabel-label': { fontSize: isMobile ? '0.875rem' : '1rem' } }}
            />
            <FormControlLabel
              value="1"
              control={<Radio size={isMobile ? 'small' : 'medium'} />}
              label={t('Warning Notification')}
              sx={{ '& .MuiFormControlLabel-label': { fontSize: isMobile ? '0.75rem' : '1rem' } }}
            />
            <FormControlLabel
              value="2"
              control={<Radio size={isMobile ? 'small' : 'medium'} />}
              label={t('Warning and Close Position')}
              sx={{ '& .MuiFormControlLabel-label': { fontSize: isMobile ? '0.75rem' : '1rem' } }}
            />
          </RadioGroup>
        </FormControl>
      )}
    />
  );

  const renderLeverage = (name) => (
    <Controller
      name={name}
      control={control}
      defaultValue={1}
      rules={{
        required: true,
        valueAsNumber: true,
        validate: {
          range: (value) =>
            (value >= 1 && value <= 20) || t('Value out of range'),
        },
      }}
      render={({ field, fieldState }) => (
        <FormControl fullWidth error={!!fieldState.error} variant="standard">
          <Stack
            direction="row"
            alignItems="flex-end"
            spacing={2}
            sx={{ mb: 2 }}
          >
            <FormLabel sx={{ fontSize: isMobile ? '0.875rem' : '1rem' }}>
              {t('Leverage')} <small style={{ fontSize: isMobile ? '0.75rem' : '0.875rem' }}>[1 ~ 20]</small>
            </FormLabel>
            <Input
              inputProps={{ min: 1, max: 20, step: 1, type: 'number' }}
              {...field}
              onChange={(e) => {
                const value = Number(e.target.value);
                field.onChange(value);
              }}
              sx={{ 
                width: '5em',
                fontSize: isMobile ? '0.875rem' : '1rem',
                '& input': {
                  fontSize: isMobile ? '0.875rem !important' : '1rem',
                }
              }}
            />
          </Stack>
          <Slider
            marks
            min={1}
            max={20}
            step={1}
            color={fieldState.error ? 'error' : 'info'}
            valueLabelDisplay="auto"
            {...field}
          />
          <FormHelperText>{fieldState.error?.message}</FormHelperText>
        </FormControl>
      )}
    />
  );

  return (
    <Box
      sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}
    >
      <Box
        component="form"
        onSubmit={handleSubmit(onSubmit)}
        sx={{ mx: 'auto' }}
      >
        {isPutTradeConfigLoading && <LinearProgress />}
        <Table
          sx={{
            mb: 3,
            tableLayout: { xs: 'fixed', md: 'auto' },
            td: { border: 1, borderColor: 'divider' },
          }}
        >
          <TableHead>
            <TableRow>
              <TableCell sx={{ width: { xs: '30%', md: 240 } }} />
              <TableCell
                align="center"
                sx={{
                  fontSize: isMobile ? 12 : 14,
                  fontWeight: 700,
                  width: { xs: '35%', md: 240 },
                }}
              >
                {marketCodeCombination.target.icon}{' '}
                {marketCodeCombination.target.getLabel()}
              </TableCell>
              <TableCell
                align="center"
                sx={{
                  fontSize: isMobile ? 12 : 14,
                  fontWeight: 700,
                  width: { xs: '30%', md: 240 },
                }}
              >
                {marketCodeCombination.origin.icon}{' '}
                {marketCodeCombination.origin.getLabel()}
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            <TableRow>
              <TableCell sx={{ fontSize: isMobile ? '0.875rem' : '1rem' }}>
                {t('Margin Mode')}
              </TableCell>
              <TableCell
                rowSpan={marketCodeCombination.target.isSpot ? 3 : undefined}
                sx={
                  marketCodeCombination.target.isSpot
                    ? { bgcolor: 'divider', opacity: 0.25 }
                    : undefined
                }
              >
                {marketCodeCombination.target.isSpot
                  ? t('The SPOT market does not require separate settings.')
                  : renderMarginMode('target_market_cross')}
              </TableCell>
              <TableCell
                rowSpan={marketCodeCombination.origin.isSpot ? 3 : undefined}
                sx={
                  marketCodeCombination.origin.isSpot
                    ? { bgcolor: 'divider', opacity: 0.25 }
                    : undefined
                }
              >
                {marketCodeCombination.origin.isSpot
                  ? t('The SPOT market does not require separate settings.')
                  : renderMarginMode('origin_market_cross')}
              </TableCell>
            </TableRow>
            <TableRow>
              <TableCell sx={{ fontSize: isMobile ? '0.875rem' : '1rem' }}>
                {t('Liquidation Detection')}
              </TableCell>
              {!marketCodeCombination.target.isSpot && (
                <TableCell>
                  {renderLiquidationDetection('target_market_margin_call')}
                </TableCell>
              )}
              {!marketCodeCombination.origin.isSpot && (
                <TableCell>
                  {renderLiquidationDetection('origin_market_margin_call')}
                </TableCell>
              )}
            </TableRow>
            <TableRow>
              <TableCell sx={{ fontSize: isMobile ? '0.875rem' : '1rem' }}>
                {t('Leverage')}
              </TableCell>
              {!marketCodeCombination.target.isSpot && (
                <TableCell>
                  {renderLeverage('target_market_leverage')}
                </TableCell>
              )}
              {!marketCodeCombination.origin.isSpot && (
                <TableCell>
                  {renderLeverage('origin_market_leverage')}
                </TableCell>
              )}
            </TableRow>
            <TableRow>
              <TableCell sx={{ fontSize: isMobile ? '0.875rem' : '1rem' }}>
                {t('Trade Failsafe')}
              </TableCell>
              <TableCell colSpan={2}>
                <Controller
                  name="safe_reverse"
                  control={control}
                  defaultValue=""
                  rules={{ required: true }}
                  render={({ field, fieldState }) => (
                    <FormControl error={!!fieldState.error} variant="standard">
                      <RadioGroup
                        row
                        {...field}
                        sx={{ textTransform: 'uppercase' }}
                      >
                        <FormControlLabel
                          value="false"
                          control={<Radio size={isMobile ? 'small' : 'medium'} />}
                          label={t('Off')}
                          sx={{ '& .MuiFormControlLabel-label': { fontSize: isMobile ? '0.875rem' : '1rem' } }}
                        />
                        <FormControlLabel
                          value="true"
                          control={<Radio size={isMobile ? 'small' : 'medium'} />}
                          label={t('On')}
                          sx={{ '& .MuiFormControlLabel-label': { fontSize: isMobile ? '0.875rem' : '1rem' } }}
                        />
                      </RadioGroup>
                    </FormControl>
                  )}
                />
              </TableCell>
            </TableRow>
            {(marketCodeCombination.target.isSpot || marketCodeCombination.origin.isSpot) && (
              <TableRow>
                <TableCell sx={{ fontSize: isMobile ? '0.875rem' : '1rem' }}>
                  {t('Repetitive Trade Condition')}
                </TableCell>
                <TableCell align="center" colSpan={2}>
                  <Controller
                    name="repeat_limit_p"
                    control={control}
                    defaultValue={0}
                    rules={{
                      required: true,
                      valueAsNumber: true,
                      validate: {
                        range: (value) =>
                          (value >= -20 && value <= 30) ||
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
                          <FormLabel sx={{ fontSize: isMobile ? '0.875rem' : '1rem' }}>
                            {t('Repetitive Trade Condition')}{' '}
                            <small style={{ fontSize: isMobile ? '0.75rem' : '0.875rem' }}>[-20% ~ 30%]</small>
                          </FormLabel>
                          <Input
                            inputProps={{
                              min: -20,
                              max: 30,
                              step: 0.1,
                              type: 'number',
                            }}
                            {...field}
                            onChange={(e) => {
                              const value = Number(e.target.value);
                              field.onChange(value);
                            }}
                            sx={{ 
                              width: '5em',
                              fontSize: isMobile ? '0.875rem' : '1rem',
                              '& input': {
                                fontSize: isMobile ? '0.875rem !important' : '1rem',
                              }
                            }}
                            slotProps={{
                              input: {
                                endAdornment: (
                                  <InputAdornment position="end" sx={{ 
                                    '& .MuiTypography-root': {
                                      fontSize: isMobile ? '1rem !important' : '1.125rem !important'
                                    }
                                  }}>%</InputAdornment>
                                ),
                              },
                            }}
                          />
                        </Stack>
                        <Slider
                          marks
                          min={-20}
                          max={30}
                          step={0.1}
                          color={fieldState.error ? 'error' : 'info'}
                          valueLabelDisplay="auto"
                          valueLabelFormat={(value) => `${value}% 이하에서만 반복거래 작동`}
                          {...field}
                        />
                        <FormHelperText>
                          {fieldState.error?.message}
                        </FormHelperText>
                      </FormControl>
                    )}
                  />
                </TableCell>
              </TableRow>
            )}
            <TableRow>
              <TableCell sx={{ fontSize: isMobile ? '0.875rem' : '1rem' }}>
                {t('Telegram Message Notification Interval')}
              </TableCell>
              <TableCell colSpan={2}>
                <Controller
                  name="send_term"
                  control={control}
                  defaultValue={0}
                  rules={{ required: true }}
                  render={({ field, fieldState }) => (
                    <TextField
                      fullWidth
                      error={!!fieldState.error}
                      size="small"
                      variant="standard"
                      InputProps={{
                        inputProps: { min: 0, step: 1, type: 'number' },
                        sx: {
                          fontSize: isMobile ? '0.875rem !important' : '1rem',
                          '& input': {
                            fontSize: isMobile ? '0.875rem !important' : '1rem',
                          }
                        }
                      }}
                      {...field}
                      sx={{ width: '12em' }}
                    />
                  )}
                />
              </TableCell>
            </TableRow>
            <TableRow>
              <TableCell sx={{ fontSize: isMobile ? '0.875rem' : '1rem' }}>
                {t('Telegram Message Alarm Count')}
              </TableCell>
              <TableCell colSpan={2}>
                <Controller
                  name="send_times"
                  control={control}
                  rules={{ required: true }}
                  defaultValue={0}
                  render={({ field, fieldState }) => (
                    <TextField
                      fullWidth
                      error={!!fieldState.error}
                      size="small"
                      variant="standard"
                      InputProps={{
                        inputProps: { min: 0, step: 1, type: 'number' },
                        sx: {
                          fontSize: isMobile ? '0.875rem !important' : '1rem',
                          '& input': {
                            fontSize: isMobile ? '0.875rem !important' : '1rem',
                          }
                        }
                      }}
                      {...field}
                      sx={{ width: '12em' }}
                    />
                  )}
                />
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
        <Box display="flex" alignItems="center" justifyContent="center">
          <Button
            type="submit"
            variant="contained"
            disabled={!isDirty || !isValid || isPutTradeConfigLoading}
            endIcon={
              isPutTradeConfigLoading ? (
                <CircularProgress color="inherit" size={15} />
              ) : (
                <ArrowForwardIcon />
              )
            }
            sx={{ px: 8 }}
          >
            {t('Update')}
          </Button>
        </Box>
      </Box>
    </Box>
  );
}
