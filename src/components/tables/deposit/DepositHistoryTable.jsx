import React, { useMemo } from 'react';

import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import { useTranslation } from 'react-i18next';

import ReactTableUI from 'components/ReactTableUI';

import renderCurrencyFormatCell from 'components/tables/common/renderCurrencyFormatCell';

import renderDepositTypeCell from './renderDepositTypeCell';

export default function DepositHistoryTable({ isLoading, tableData }) {
  const { i18n, t } = useTranslation();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const columns = useMemo(
    () => [
      {
        accessorKey: 'balance',
        size: isMobile ? 40 : 60,
        header: t('Balance'),
        cell: renderCurrencyFormatCell,
      },
      {
        accessorKey: 'change',
        size: isMobile ? 40 : 60,
        header: t('Change'),
        cell: renderCurrencyFormatCell,
      },
      {
        accessorKey: 'txid',
        size: isMobile ? 60 : 180,
        header: t('TXID'),
      },
      {
        accessorKey: 'type',
        size: isMobile ? 40 : 80,
        header: t('Type'),
        cell: renderDepositTypeCell,
      },
      {
        accessorKey: 'registered_datetime',
        size: isMobile ? 40 : 80,
        header: t('Date'),
        // cell: renderDateCell,
      },
    ],
    [i18n.language]
  );

  return (
    <ReactTableUI
      columns={columns}
      data={tableData}
      isLoading={isLoading}
      showProgressBar={isLoading}
      getCellProps={() => ({ sx: { textAlign: 'center', py: 1 } })}
      getHeaderProps={() => ({ sx: { textAlign: 'center' } })}
    />
  );
}
