import React, { useMemo } from 'react';

import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { useTranslation } from 'react-i18next';

import { useGetDepositHistoryQuery } from 'redux/api/drf/user';

import { DateTime } from 'luxon';

import DepositHistoryTable from 'components/tables/deposit/DepositHistoryTable';

export default function DepositHistory() {
  const { i18n, t } = useTranslation();

  const { data, isFetching } = useGetDepositHistoryQuery();

  const tableData = useMemo(
    () =>
      (data?.results?.map((item) => ({
        ...item,
        balance: parseFloat(item.balance || 0),
        change: parseFloat(item.change || 0),
        registered_datetime: DateTime.fromISO(item.registered_datetime, {
          zone: 'local',
        }).toLocaleString(DateTime.DATETIME_MED),
        // Keep original datetime for sorting
        original_datetime: DateTime.fromISO(item.registered_datetime, {
          zone: 'local',
        }),
      })) || [])
      .sort((a, b) => b.original_datetime.toMillis() - a.original_datetime.toMillis()),
    [data, i18n]
  );

  return (
    <Box
      sx={{
        mx: 'auto',
        mt: { xs: 4, md: 0 },
        width: { xs: '100%', md: '90%' },
      }}
    >
      <Typography variant="h6" sx={{ mb: 4, textAlign: 'center' }}>
        {t('Deposit History')}
      </Typography>
      <DepositHistoryTable tableData={tableData} isLoading={isFetching} />
    </Box>
  );
}
