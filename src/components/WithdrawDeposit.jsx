import React, { useMemo, useState, useEffect } from 'react';
import { useSelector } from 'react-redux';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import FormControl from '@mui/material/FormControl';
import FormHelperText from '@mui/material/FormHelperText';
import InputLabel from '@mui/material/InputLabel';
import OutlinedInput from '@mui/material/OutlinedInput';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import { WITHDRAWAL_TYPE } from 'constants';

import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

import { useTranslation } from 'react-i18next';

import { Controller, useForm } from 'react-hook-form';

import { DateTime } from 'luxon';

import {
  useGetWithdrawalRequestsQuery,
  usePostWithdrawalRequestMutation,
  useGetDepositBalanceQuery,
} from 'redux/api/drf/user';

import {
  useGetWalletBalanceQuery,
} from 'redux/api/drf/wallet';

import ReactTableUI from 'components/ReactTableUI';
import renderCurrencyFormatCell from 'components/tables/common/renderCurrencyFormatCell';
import renderTruncatedCell from 'components/tables/common/renderTruncatedCell';
import renderWithdrawalStatusCell from 'components/tables/deposit/renderWithdrawalStatusCell';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';

export default function WithdrawDeposit() {
  const theme = useTheme();
  const { user } = useSelector((state) => state.auth);
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const { t } = useTranslation();
  const [withdrawableUsdt, setWithdrawableUsdt] = useState(0);
  const [withdrawableCommission, setWithdrawableCommission] = useState(0);
  const [pagination, setPagination] = useState({
    pageIndex: 0,
    pageSize: 20,
  });

  // Configure if TRX is sufficient
  const minimumTrxRequired = 30;

  // Form handling
  const {
    control,
    formState: { errors, isValid },
    handleSubmit,
    reset,
    watch,
  } = useForm({
    defaultValues: {
      amount: '',
      address: '',
      type: 'DEPOSIT', // Changed to lowercase
    },
    mode: 'onChange',
  });

  // Watch selected type
  const selectedType = watch('type');

  // API hooks
  const [postWithdrawalRequest, { isLoading: isPostLoading }] = usePostWithdrawalRequestMutation();
  const { data: withdrawalRequests, isLoading } = useGetWithdrawalRequestsQuery({}, {
    skip: !user,
    pollingInterval: 1000 * 5, // Poll every 5 seconds
  });

  const { data: walletTrxBalance } = useGetWalletBalanceQuery(
    {
      userUuid: user?.uuid,
      asset: 'TRX',
    },
    { 
      skip: !user,
      pollingInterval: 1000 * 60 // 60 seconds
    }
  );

  const { data: walletWithdrawableUsdtBalance } = useGetDepositBalanceQuery(
    {},
    { 
      skip: !user,
      pollingInterval: 1000 * 60 // 60 seconds
    }
  );

  useEffect(() => {
    if (walletWithdrawableUsdtBalance?.results?.length) {
      const ownBalance = walletWithdrawableUsdtBalance.results.find((item) => item.user === user.uuid);
      setWithdrawableUsdt(ownBalance.withdrawable_balance);
      setWithdrawableCommission(ownBalance.withdrawable_commission);
    }
  }, [walletWithdrawableUsdtBalance, user]);

  const trxInsufficient = walletTrxBalance?.balance !== undefined && walletTrxBalance.balance < minimumTrxRequired;

  // Table columns
  const columns = useMemo(
    () => [
      {
        accessorKey: 'type',
        size: isMobile ? 40 : 60,
        header: t('Type'),
      },
      {
        accessorKey: 'amount',
        size: isMobile ? 40 : 60,
        header: t('Amount'),
        cell: renderCurrencyFormatCell,
      },
      {
        accessorKey: 'address',
        size: isMobile ? 60 : 180,
        header: t('To Address'),
        cell: renderTruncatedCell,
      },
      {
        accessorKey: 'txid',
        size: isMobile ? 60 : 180,
        header: t('TXID'),
        cell: renderTruncatedCell,
      },
      {
        accessorKey: 'status',
        size: isMobile ? 40 : 80,
        header: t('Status'),
        cell: renderWithdrawalStatusCell,
      },
      {
        accessorKey: 'requested_datetime',
        size: isMobile ? 40 : 80,
        header: t('Date'),
      },
    ],
    [isMobile, t]
  );

  // Table data processing
  const tableData = useMemo(
    () =>
      (withdrawalRequests?.results?.map((item) => ({
        ...item,
        requested_datetime: DateTime.fromISO(item.requested_datetime, {
          zone: 'local',
        }).toLocaleString(DateTime.DATETIME_MED),
        // Keep original for sorting
        original_datetime: DateTime.fromISO(item.requested_datetime),
      })) || [])
      .sort((a, b) => b.original_datetime.toMillis() - a.original_datetime.toMillis()),
    [withdrawalRequests]
  );

  // Form submission handler
  const onSubmit = async (data) => {
    try {
      await postWithdrawalRequest({
        amount: parseFloat(data.amount),
        address: data.address,
        type: data.type,  // Use the selected type
      }).unwrap();
      reset();
    } catch (err) {
      // Removed unexpected console statement
    }
  };

  // Conditionally render title
  const title = selectedType === 'DEPOSIT' ? t('Withdraw Deposit') : t('Withdraw Commission');
  const withdrawableTitle = selectedType === 'DEPOSIT' ? t('Your Withdrawable USDT Balance') : t('Your Withdrawable Commission Balance');
  const withdrawableAmount = selectedType === 'DEPOSIT' ? withdrawableUsdt : withdrawableCommission;

  return (
    <Box sx={{ p: 2 }}>
      {/* Current Balances and Requirements */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="body1">
          {t('Your TRX Balance')}: {walletTrxBalance?.balance ?? 0}
        </Typography>
        <Typography variant="body1">
          {withdrawableTitle}: {withdrawableAmount}
        </Typography>
        {trxInsufficient && (
          <FormHelperText error>
            {t('You need at least {{minimumTrxRequired}} TRX to cover network fees. Please deposit TRX first.', { minimumTrxRequired })}
          </FormHelperText>
        )}
      </Box>

      {/* Withdrawal Request Form */}
      <Box
        component="form"
        onSubmit={handleSubmit(onSubmit)}
        sx={{
          mb: 4,
          mx: 'auto',
          width: { xs: '100%', md: '50%' },
        }}
      >
        <Typography variant="h6" sx={{ mb: 4, textAlign: 'center' }}>
          {title}
        </Typography>
        
        <Stack spacing={3}>
          <Controller
            name="type"
            control={control}
            rules={{ required: t('Type is required') }}
            render={({ field }) => (
              <FormControl variant="outlined">
                <InputLabel>{t('Type')}</InputLabel>
                <Select {...field} label={t('Type')}>
                  {Object.entries(WITHDRAWAL_TYPE).map(([key, typeObj]) => (
                    <MenuItem
                      key={key}
                      value={key}
                      disabled={key === 'COMMISSION' && withdrawableCommission <= 0}
                      >
                      {t(typeObj.getLabel())}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
          />

          <Controller
            name="amount"
            control={control}
            rules={{
              required: t('Amount is required'),
              min: { value: 1, message: t('Minimum amount is 1') },
              max: 
              { 
                value: withdrawableUsdt || 0,
                message: t('You can not withdraw more than {{withdrawableUsdt}} USDT', { withdrawableUsdt })
              },
            }}
            render={({ field }) => (
              <FormControl error={!!errors.amount} variant="outlined">
                <InputLabel>{t('Amount')}</InputLabel>
                <OutlinedInput
                  {...field}
                  type="number"
                  label={t('Amount')}
                  inputProps={{ min: 1, step: 1 }}
                />
                {errors.amount && (
                  <FormHelperText>{errors.amount.message}</FormHelperText>
                )}
              </FormControl>
            )}
          />

          <Controller
            name="address"
            control={control}
            rules={{
              required: t('Wallet address is required'),
              validate: (value) => {
                // Handle case where TronWeb might not be loaded
                if (!value) return true;
                try {
                  // Access isAddress from TronWeb constructor
                  return window.tronWeb?.isAddress(value) || t('Invalid TRC20(TRX) network address');
                } catch (error) {
                  // Removed unexpected console statement
                  return t('Unable to validate address');
                }
              },
            }}
            render={({ field }) => (
              <FormControl error={!!errors.address} variant="outlined">
                <InputLabel>{t('To Address')}</InputLabel>
                <OutlinedInput
                  {...field}
                  label={t('To Address')}
                />
                {errors.address && (
                  <FormHelperText>{errors.address.message}</FormHelperText>
                )}
              </FormControl>
            )}
          />

          <Button
            disabled={!isValid || isPostLoading || trxInsufficient}
            type="submit"
            variant="contained"
            size="large"
          >
            {t('Request Withdrawal')}
          </Button>
        </Stack>
      </Box>

      {/* Withdrawal History Table */}
      <Box sx={{ mt: 4 }}>
        <Typography variant="h6" sx={{ mb: 4, textAlign: 'center' }}>
          {t('Withdrawal History')}
        </Typography>
        
        <ReactTableUI
          columns={columns}
          data={tableData}
          isLoading={isLoading}
          showProgressBar={isLoading}
          enableTablePaginationUI
          options={{
            state: { pagination },
            onPaginationChange: setPagination,
            pageCount: Math.ceil(tableData.length / pagination.pageSize),
          }}
          getCellProps={() => ({ sx: { textAlign: 'center', py: 1 } })}
          getHeaderProps={() => ({ sx: { textAlign: 'center' } })}
        />
      </Box>
    </Box>
  );
}