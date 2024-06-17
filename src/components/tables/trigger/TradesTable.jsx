import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';

import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import { useTranslation } from 'react-i18next';
import { DateTime } from 'luxon';

import {
  useDeleteMultipleTradesMutation,
  useGetTradesByTradeConfigQuery,
} from 'redux/api/drf/tradecore';

import isEmpty from 'lodash/isEmpty';
import orderBy from 'lodash/orderBy';

import DeleteAlert from 'components/DeleteAlert';
import ReactTableUI from 'components/ReactTableUI';
import UpdateTriggerForm from 'components/UpdateTriggerForm';

import renderCurrencyFormatCell from 'components/tables/common/renderCurrencyFormatCell';
import renderExpandCell from 'components/tables/common/renderExpandCell';
import renderSelectCell from './renderSelectCell';
import renderStatusCell from './renderStatusCell';
import renderValueCell from './renderValueCell';

import renderSelectHeader from './renderSelectHeader';

export default function TradesTable({
  baseAsset,
  tradeConfigAllocation,
  tradeType,
  onTriggerConfigChange,
  createTriggerFormRef,
}) {
  const tableRef = useRef();
  const { i18n, t } = useTranslation();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [expanded, setExpanded] = useState({});
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 10 });
  const [rowSelection, setRowSelection] = useState({});

  const [deleteAlert, setDeleteAlert] = useState(false);

  const {
    data: trades,
    isFetching,
    isLoading,
  } = useGetTradesByTradeConfigQuery(
    {
      baseAsset,
      tradeConfigUuid: tradeConfigAllocation?.trade_config_uuid,
    },
    { skip: !tradeConfigAllocation, pollingInterval: 1000 * 60 }
  );

  const [
    deleteMultipleTrades,
    { isLoading: isDeleteLoading, isSuccess: isDeleteSuccess },
  ] = useDeleteMultipleTradesMutation();

  useEffect(() => {
    if (isDeleteSuccess) {
      tableRef.current?.toggleAllRowsSelected(false);
      setDeleteAlert(false);
    }
  }, [isDeleteSuccess]);

  useEffect(() => {
    if (!isEmpty(expanded)) createTriggerFormRef.current.setDisabled(true);
    else createTriggerFormRef.current.setDisabled(false);
  }, [expanded]);

  const columns = useMemo(
    () => [
      {
        accessorKey: 'select',
        enableSorting: false,
        size: isMobile ? 10 : 50,
        header: renderSelectHeader,
        cell: renderSelectCell,
      },
      {
        accessorKey: 'entry',
        size: isMobile ? 80 : 120,
        header: t('Entry'),
        cell: renderValueCell,
      },
      {
        accessorKey: 'exit',
        size: isMobile ? 80 : 120,
        header: t('Exit'),
        cell: renderValueCell,
      },
      ...(tradeType === 'autoTrade'
        ? [
            {
              accessorKey: 'tradeCapital',
              size: isMobile ? 80 : 120,
              header: t('Trade Capital'),
              cell: renderCurrencyFormatCell,
            },
          ]
        : []),
      {
        accessorKey: 'status',
        size: isMobile ? 80 : 140,
        header: t('Status'),
        cell: renderStatusCell,
      },
      {
        accessorKey: 'created',
        header: t('Created'),
      },
      {
        accessorKey: 'edit',
        enableGlobalFilter: false,
        enableSorting: false,
        size: 11,
        maxSize: 11,
        cell: renderExpandCell,
        header: <span />,
      },
    ],
    [i18n.language, isMobile, tradeType]
  );

  const data = useMemo(
    () =>
      orderBy(
        trades?.filter((i) => {
          if (tradeType === 'alarm') return i.trade_capital === null;
          if (tradeType === 'autoTrade') return i.trade_capital !== null;
          return true;
        }) || [],
        'registered_datetime',
        'desc'
      ).map((trade) => ({
        ...trade,
        baseAsset: trade.base_asset,
        entry: trade.low,
        exit: trade.high,
        created: DateTime.fromISO(trade.registered_datetime, {
          zone: 'UTC',
        })
          .toLocal()
          .toLocaleString(DateTime.DATETIME_MED),
        status: trade.trade_switch,
        tradeCapital: trade.trade_capital,
        isTether: trade.usdt_conversion,
        isDeleteLoading,
      })),
    [trades, tradeType, isDeleteLoading]
  );

  const getRowId = useCallback((row) => row.uuid, []);
  const onExpandedChange = useCallback(
    (newExpanded) => setExpanded(newExpanded()),
    []
  );

  const renderSubComponent = useCallback(
    ({ row: { original, toggleExpanded }, meta }) => (
      <Box sx={{ bgcolor: 'background.default' }}>
        <UpdateTriggerForm
          baseAsset={original.baseAsset}
          defaultEntry={original.entry}
          defaultExit={original.exit}
          defaultTradeCapital={original.trade_capital}
          isTether={original.isTether}
          tradeConfigUuid={original.trade_config_uuid}
          usdtConversion={original.usdt_conversion}
          uuid={original.uuid}
          onTriggerConfigChange={meta.onTriggerConfigChange}
          toggleExpanded={toggleExpanded}
          tradeType={original.trade_capital !== null ? 'autoTrade' : 'alarm'}
        />
      </Box>
    ),
    []
  );

  return (
    <Box sx={{ mx: { xs: 0, md: 4 }, p: { xs: 0, md: 2 } }}>
      {Object.keys(rowSelection).length > 0 && (
        <Stack alignItems="center" direction="row" spacing={2} sx={{ mb: 2 }}>
          <Typography sx={{ fontWeight: 700 }}>
            {t('{{selected}} of {{total}} selected', {
              selected: Object.keys(rowSelection).length,
              total: data.length,
            })}
          </Typography>
          <IconButton
            aria-label="Delete selected"
            color={deleteAlert || isDeleteLoading ? 'error' : 'secondary'}
            onClick={() => setDeleteAlert(true)}
            sx={{ p: 0, ':hover': { color: 'error.main' } }}
          >
            <DeleteIcon />
          </IconButton>
        </Stack>
      )}
      <ReactTableUI
        enableTablePaginationUI
        ref={tableRef}
        columns={columns}
        data={data}
        isLoading={isLoading}
        showProgressBar={isFetching}
        options={{
          getRowId,
          enableRowSelection: true,
          state: { expanded, pagination, rowSelection },
          onExpandedChange,
          onPaginationChange: setPagination,
          onRowSelectionChange: setRowSelection,
          meta: {
            theme,
            isMobile,
            onTriggerConfigChange,
            expandIcon: EditIcon,
          },
        }}
        renderSubComponent={renderSubComponent}
        getHeaderProps={() => ({
          sx: {
            bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.100',
            px: { xs: 0, md: 2 },
          },
        })}
        getCellProps={() => ({ sx: { height: 30, px: { xs: 0, md: 2 } } })}
        getRowProps={(row) => ({
          onClick: () => row.toggleExpanded(!row.getIsExpanded()),
          sx: {
            cursor: 'pointer',
            ...(row.getIsExpanded()
              ? { bgcolor: theme.palette.background.default }
              : {}),
          },
        })}
        getTableProps={() => ({
          sx: {
            border: 1,
            borderColor: 'divider',
            fontSize: '1em',
            width: isMobile ? 'auto' : undefined,
          },
        })}
      />
      <DeleteAlert
        loading={isDeleteLoading}
        open={deleteAlert}
        title={t(
          'Are you sure you want to permanently delete the selected alarm(s)?'
        )}
        onCancel={() => setDeleteAlert(false)}
        onClose={() => setDeleteAlert(isDeleteLoading)}
        onDelete={() =>
          deleteMultipleTrades(
            Object.keys(rowSelection).map((row) => ({
              uuid: row,
              params: {
                tradeConfigUuid: tradeConfigAllocation?.trade_config_uuid,
              },
            }))
          )
        }
      />
    </Box>
  );
}
