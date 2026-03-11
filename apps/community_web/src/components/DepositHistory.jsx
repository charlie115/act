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
    () => {
      try {
        return (data?.results?.map((item) => {
          let originalDateTime;
          try {
            // Convert string to DateTime object
            originalDateTime = item.registered_datetime ? 
              DateTime.fromISO(item.registered_datetime) : 
              DateTime.local();
          } catch (e) {
            // Fallback if DateTime creation fails
            originalDateTime = { toMillis: () => 0 };
          }
          
          return {
            ...item,
            balance: parseFloat(item.balance || 0),
            change: parseFloat(item.change || 0),
            registered_datetime: item.registered_datetime,
            // Store the DateTime object for sorting
            original_datetime: originalDateTime,
          };
        }) || [])
        .sort((a, b) => {
          try {
            return b.original_datetime.toMillis() - a.original_datetime.toMillis();
          } catch (e) {
            // Fallback sorting if toMillis fails
            return 0;
          }
        });
      } catch (error) {
        console.error("Error processing deposit history data:", error);
        return [];
      }
    },
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
