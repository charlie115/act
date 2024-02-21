import React, { useEffect, useState } from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import FormControl from '@mui/material/FormControl';
import IconButton from '@mui/material/IconButton';
import Input from '@mui/material/Input';
import Stack from '@mui/material/Stack';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';

import CheckIcon from '@mui/icons-material/Check';
import CloseIcon from '@mui/icons-material/Close';
import EditIcon from '@mui/icons-material/Edit';
import Replay5Icon from '@mui/icons-material/Replay5';
import SyncAltIcon from '@mui/icons-material/SyncAlt';
import TimesOneMobiledataIcon from '@mui/icons-material/TimesOneMobiledata';

import { Controller, useForm } from 'react-hook-form';

import {
  useGetTradeConfigQuery,
  usePutTradeConfigMutation,
} from 'redux/api/drf/tradecore';

import { useTranslation } from 'react-i18next';

export default function BotSettings({
  marketCodeSelectorRef,
  selectedMarketCodeCombination,
}) {
  const { t } = useTranslation();

  const [isEditingCount, setIsEditingCount] = useState(false);
  const [isEditingInterval, setIsEditingInterval] = useState(false);

  const [putTradeConfig] = usePutTradeConfigMutation();

  const { data } = useGetTradeConfigQuery(
    { uuid: selectedMarketCodeCombination?.tradeConfigUuid },
    { skip: !selectedMarketCodeCombination?.tradeConfigUuid }
  );

  const countForm = useForm({
    defaultValues: { count: data?.send_times },
    mode: 'all',
  });
  const onCountSubmit = async (formData) => {
    try {
      await putTradeConfig({
        uuid: data.uuid,
        acw_user_uuid: data.acw_user_uuid,
        target_market_code: data.target_market_code,
        origin_market_code: data.origin_market_code,
        send_times: formData.count,
      });
      countForm.reset();
      setIsEditingCount(false);
    } catch (err) {
      /* empty */
    }
  };

  const intervalForm = useForm({
    defaultValues: { interval: data?.send_term },
    mode: 'all',
  });
  const onIntervalSubmit = async (formData) => {
    try {
      await putTradeConfig({
        uuid: data.uuid,
        acw_user_uuid: data.acw_user_uuid,
        target_market_code: data.target_market_code,
        origin_market_code: data.origin_market_code,
        send_term: formData.interval,
      });
      intervalForm.reset();
      setIsEditingInterval(false);
    } catch (err) {
      /* empty */
    }
  };

  useEffect(() => {
    if (data) {
      countForm.setValue('count', data.send_times);
      intervalForm.setValue('interval', data.send_term);
    }
  }, [data]);

  return (
    <Box
      sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}
    >
      <Box sx={{ mx: 'auto', my: 4 }}>
        {selectedMarketCodeCombination?.value === 'ALL' ? (
          <Button
            color="secondary"
            onClick={() => marketCodeSelectorRef.current.toggle()}
            sx={{ borderBottom: 1, borderRadius: 0 }}
          >
            {t('Please select a specific market combination')}
          </Button>
        ) : (
          <Table
            sx={{
              borderCollapse: 'collapse',
              mt: 3,
              td: { border: 0 },
            }}
          >
            <TableHead sx={{ mb: 3 }}>
              <TableRow>
                <TableCell colSpan="4">
                  <Stack
                    direction="row"
                    justifyContent="center"
                    spacing={1}
                    onClick={() => marketCodeSelectorRef.current.toggle()}
                  >
                    {selectedMarketCodeCombination?.target.icon}
                    <Box>{selectedMarketCodeCombination?.target.label}</Box>
                    <SyncAltIcon color="accent" fontSize="small" />
                    {selectedMarketCodeCombination?.origin.icon}
                    <Box>{selectedMarketCodeCombination?.origin.label}</Box>
                  </Stack>
                </TableCell>
              </TableRow>
            </TableHead>
            {data && (
              <TableBody>
                <TableRow
                  sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                >
                  <TableCell align="right" sx={{ p: 0, width: 16 }}>
                    <TimesOneMobiledataIcon />
                  </TableCell>
                  <TableCell sx={{ fontSize: 16 }}>
                    {t('Telegram Message Alarm Count')}
                  </TableCell>
                  <TableCell
                    align="right"
                    sx={{ fontSize: 16, fontWeight: 700, width: 120 }}
                  >
                    {isEditingCount ? (
                      <Box
                        id="update-count-form"
                        component="form"
                        autoComplete="off"
                        onSubmit={countForm.handleSubmit(onCountSubmit)}
                      >
                        <Controller
                          name="count"
                          control={countForm.control}
                          rules={{ required: true }}
                          render={({ field, fieldState }) => (
                            <FormControl
                              error={!!fieldState.error}
                              variant="standard"
                            >
                              <Input
                                autoFocus
                                // readOnly={isLoading}
                                type="number"
                                inputProps={{ step: 1 }}
                                {...field}
                              />
                            </FormControl>
                          )}
                        />
                      </Box>
                    ) : (
                      data.send_times
                    )}
                  </TableCell>
                  <TableCell sx={{ width: 80 }}>
                    {isEditingCount ? (
                      <Stack alignItems="center" direction="row" spacing={0}>
                        <IconButton
                          color="success"
                          type="submit"
                          form="update-count-form"
                        >
                          <CheckIcon />
                        </IconButton>
                        <IconButton
                          color="error"
                          onClick={() => setIsEditingCount(false)}
                        >
                          <CloseIcon />
                        </IconButton>
                      </Stack>
                    ) : (
                      <IconButton
                        size="small"
                        onClick={() => setIsEditingCount(true)}
                      >
                        <EditIcon />
                      </IconButton>
                    )}
                  </TableCell>
                </TableRow>
                <TableRow
                  sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                >
                  <TableCell align="right" sx={{ p: 0, width: 16 }}>
                    <Replay5Icon />
                  </TableCell>
                  <TableCell sx={{ fontSize: 16 }}>
                    {t('Telegram Message Notification Interval')}
                  </TableCell>
                  <TableCell
                    align="right"
                    sx={{ fontSize: 16, fontWeight: 700, width: 120 }}
                  >
                    {isEditingInterval ? (
                      <Box
                        id="update-interval-form"
                        component="form"
                        autoComplete="off"
                        onSubmit={intervalForm.handleSubmit(onIntervalSubmit)}
                      >
                        <Controller
                          name="interval"
                          control={intervalForm.control}
                          rules={{ required: true }}
                          render={({ field, fieldState }) => (
                            <FormControl
                              error={!!fieldState.error}
                              variant="standard"
                            >
                              <Input
                                autoFocus
                                // readOnly={isLoading}
                                type="number"
                                inputProps={{ step: 1 }}
                                {...field}
                              />
                            </FormControl>
                          )}
                        />
                      </Box>
                    ) : (
                      data.send_term
                    )}
                  </TableCell>
                  <TableCell sx={{ width: 80 }}>
                    {isEditingInterval ? (
                      <Stack alignItems="center" direction="row" spacing={0}>
                        <IconButton
                          color="success"
                          type="submit"
                          form="update-interval-form"
                        >
                          <CheckIcon />
                        </IconButton>
                        <IconButton
                          color="error"
                          onClick={() => setIsEditingInterval(false)}
                        >
                          <CloseIcon />
                        </IconButton>
                      </Stack>
                    ) : (
                      <IconButton
                        size="small"
                        onClick={() => setIsEditingInterval(true)}
                      >
                        <EditIcon />
                      </IconButton>
                    )}
                  </TableCell>
                </TableRow>
              </TableBody>
            )}
          </Table>
        )}
      </Box>
    </Box>
  );
}
