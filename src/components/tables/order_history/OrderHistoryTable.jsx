import React, { useCallback, useMemo, useRef } from 'react';

import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import { useTranslation } from 'react-i18next';

import { useGetOrderHistoryByUuidQuery } from 'redux/api/drf/tradecore';

import ReactTableUI from 'components/ReactTableUI';

import renderDateCell from 'components/tables/common/renderDateCell';

export default function OrderHistoryTable({ tradeConfigUuid, uuid }) {
  const tableRef = useRef();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const { i18n, t } = useTranslation();

  // const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 5 });

  const { data, isFetching } = useGetOrderHistoryByUuidQuery(
    {
      uuid,
      tradeConfigUuid,
    },
    { skip: !uuid }
  );

  const columns = useMemo(
    () => [
      {
        accessorKey: 'datetime',
        size: isMobile ? 30 : 80,
        header: t('Transaction Date'),
        cell: renderDateCell,
      },
      {
        accessorKey: 'order_id',
        size: isMobile ? 40 : 120,
        header: t('Order ID'),
      },
      {
        accessorKey: 'order_type',
        size: isMobile ? 40 : 120,
        header: t('Order Type'),
      },
      {
        accessorKey: 'side',
        size: isMobile ? 30 : 60,
        header: t('Side'),
      },
      {
        accessorKey: 'market_code',
        size: isMobile ? 40 : 120,
        header: t('Market Code'),
      },
      {
        accessorKey: 'symbol',
        size: isMobile ? 30 : 60,
        header: t('Symbol'),
      },
      {
        accessorKey: 'price',
        size: isMobile ? 30 : 60,
        header: t('Price'),
        slotProps: { cell: { sx: { fontWeight: 700 } } },
      },
      {
        accessorKey: 'qty',
        size: isMobile ? 30 : 60,
        header: t('Quantity'),
        slotProps: { cell: { sx: { fontWeight: 700 } } },
      },
    ],
    [i18n.language, isMobile]
  );

  const tableData = useMemo(
    () =>
      (data ? [data] : []).map((item) => ({
        ...item,
        datetime: item.registered_datetime,
      })),
    [data, isMobile]
  );

  const getRowId = useCallback((row) => row.order_id, []);

  return (
    <ReactTableUI
      // enableTablePaginationUI
      ref={tableRef}
      columns={columns}
      data={tableData}
      options={{
        getRowId,
        // state: { pagination },
        // onExpandedChange: (newExpanded) => setExpanded(newExpanded()),
        // onPaginationChange: setPagination,
      }}
      getCellProps={() => ({ onClick: () => {}, sx: { height: 40 } })}
      showProgressBar={isFetching}
      isLoading={isFetching}
    />
  );
}
