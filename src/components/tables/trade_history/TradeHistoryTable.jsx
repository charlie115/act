import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

import useMediaQuery from '@mui/material/useMediaQuery';
import { alpha, useTheme } from '@mui/material/styles';

import { useTranslation } from 'react-i18next';

import {
  useGetTradeHistoryQuery,
  useGetTradeHistoryByUuidQuery,
  useLazyGetPnlHistoryQuery,
} from 'redux/api/drf/tradecore';

import { DateTime } from 'luxon';

import isFunction from 'lodash/isFunction';
import orderBy from 'lodash/orderBy';
import truncate from 'lodash/truncate';

import ReactTableUI from 'components/ReactTableUI';

import OrderHistoryTable from 'components/tables/order_history/OrderHistoryTable';

import renderColoredSignedNumberCell from 'components/tables/common/renderColoredSignedNumberCell';
import renderDateCell from 'components/tables/common/renderDateCell';
import renderUuidCell from 'components/tables/common/renderUuidCell';

import renderIdCell from './renderIdCell';
import renderOrderIdHeader from './renderOrderIdHeader';

export default function TradeHistoryTable({
  baseAsset,
  tradeConfigUuid,
  tradeUuid,
  uuid,
  marketCodes,
  withPnlHistory,
  withOrderHistory,
}) {
  const tableRef = useRef();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const { i18n, t } = useTranslation();

  const [expanded, setExpanded] = useState({});
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 5 });

  const [pnlTableData, setPnlTableData] = useState([]);

  const [selectedUuid, setSelectedUuid] = useState({});

  const [selectedTradeHistoryPair, setSelectedTradeHistoryPair] = useState();

  const { data, isFetching } = useGetTradeHistoryQuery(
    {
      baseAsset,
      tradeConfigUuid,
      tradeUuid,
    },
    { skip: !!uuid }
  );

  const { data: dataByUuid, isFetching: isFetchingByUuid } =
    useGetTradeHistoryByUuidQuery({ uuid, tradeConfigUuid }, { skip: !uuid });

  const [getPnlHistory] = useLazyGetPnlHistoryQuery();

  const columns = useMemo(
    () => [
      {
        accessorKey: 'datetime',
        enableSorting: false,
        size: isMobile ? 25 : 80,
        header: t('Transaction Date'),
        cell: renderDateCell,
      },
      {
        accessorKey: 'uuid',
        enableSorting: false,
        size: isMobile ? 30 : 120,
        header: t('ID'),
        ...(withPnlHistory ? { cell: renderIdCell } : {}),
      },
      {
        accessorKey: 'target_order_id',
        enableSorting: false,
        size: isMobile ? 30 : 120,
        header: renderOrderIdHeader,
        ...(withOrderHistory ? { cell: renderUuidCell } : {}),
      },
      {
        accessorKey: 'origin_order_id',
        enableSorting: false,
        size: isMobile ? 30 : 120,
        header: renderOrderIdHeader,
        ...(withOrderHistory ? { cell: renderUuidCell } : {}),
      },
      {
        accessorKey: 'target_premium_value',
        enableSorting: false,
        size: isMobile ? 25 : 60,
        header: t('Target Premium Value'),
      },
      {
        accessorKey: 'executed_premium_value',
        enableSorting: false,
        size: isMobile ? 25 : 60,
        header: t('Executed Premium Value'),
      },
      {
        accessorKey: 'slippage_p',
        enableSorting: false,
        size: isMobile ? 25 : 60,
        header: t('Slippage'),
        cell: renderColoredSignedNumberCell,
      },
      {
        accessorKey: 'trade_side',
        enableSorting: false,
        size: isMobile ? 30 : 60,
        header: t('Direction'),
        slotProps: { cell: { sx: { fontWeight: 700 } } },
      },
    ],
    [withOrderHistory, i18n.language, isMobile]
  );

  const tableData = useMemo(
    () =>
      dataByUuid
        ? [
            {
              ...dataByUuid,
              datetime: dataByUuid.registered_datetime,
            },
          ]
        : orderBy(
            data || [],
            (o) => DateTime.fromISO(o.registered_datetime).toMillis(),
            'desc'
          ).map((item) => {
            let bgcolor;
            switch (item.trade_side) {
              case 'ENTER':
                bgcolor = alpha(
                  theme.palette.success.main,
                  0.15
                  // idx === 0 ? 0.25 : 0.15
                );
                break;
              case 'EXIT':
                bgcolor = alpha(
                  theme.palette.info.main,
                  0.15
                  // idx === 0 ? 0.25 : 0.15
                );
                break;
              default:
                break;
            }
            return {
              ...item,
              datetime: item.registered_datetime,
              bgcolor,
            };
          }),
    [data, dataByUuid, isMobile]
  );

  const pnlColumns = useMemo(
    () => [
      {
        accessorKey: 'datetime',
        enableSorting: false,
        size: isMobile ? 30 : 80,
        header: t('Transaction Date'),
        cell: renderDateCell,
      },
      {
        accessorKey: 'uuid',
        enableSorting: false,
        size: isMobile ? 40 : 120,
        header: t('ID'),
      },
      {
        accessorKey: 'trade_uuid',
        enableSorting: false,
        size: isMobile ? 40 : 120,
        header: t('Trade ID'),
      },
      {
        accessorKey: 'enter_trade_history_uuid',
        enableSorting: false,
        size: isMobile ? 40 : 120,
        header: t('Enter Trade History ID'),
        cell: renderIdCell,
      },
      {
        accessorKey: 'exit_trade_history_uuid',
        enableSorting: false,
        size: isMobile ? 40 : 120,
        header: t('Exit Trade History ID'),
        cell: renderIdCell,
      },
      {
        accessorKey: 'realized_premium_gap_p',
        enableSorting: false,
        size: isMobile ? 30 : 80,
        header: t('Realized Premium Gap (%)'),
        cell: renderColoredSignedNumberCell,
      },
      {
        accessorKey: 'total_currency',
        enableSorting: false,
        size: isMobile ? 30 : 60,
        header: t('Total Currency'),
      },
      {
        accessorKey: 'total_pnl',
        enableSorting: false,
        size: isMobile ? 30 : 75,
        header: t('Total PnL'),
        cell: renderColoredSignedNumberCell,
      },
      {
        accessorKey: 'total_pnl_after_fee',
        enableSorting: false,
        size: isMobile ? 30 : 80,
        header: t('Total PnL After Fee'),
        cell: renderColoredSignedNumberCell,
      },
      {
        accessorKey: 'total_pnl_after_fee_kimp',
        enableSorting: false,
        size: isMobile ? 30 : 80,
        header: t('Total PnL After Fee KIMP'),
      },
    ],
    [i18n.language, isMobile]
  );

  const handleGetPnlHistory = async ({
    id,
    original,
    getIsExpanded,
    toggleExpanded,
  }) => {
    if (
      getIsExpanded() ||
      id === selectedTradeHistoryPair?.enter ||
      id === selectedTradeHistoryPair?.exit
    ) {
      toggleExpanded(false);
      setSelectedTradeHistoryPair();
      return;
    }
    if (
      !getIsExpanded() &&
      id !== selectedTradeHistoryPair?.enter &&
      id !== selectedTradeHistoryPair?.exit
    ) {
      setSelectedTradeHistoryPair();
      toggleExpanded(true);
    }

    const params = { tradeConfigUuid: original.trade_config_uuid };
    if (original.trade_side === 'ENTER')
      params.enter_trade_history_uuid = original.uuid;
    else if (original.trade_side === 'EXIT')
      params.exit_trade_history_uuid = original.uuid;
    try {
      const pnlData = await getPnlHistory(params).unwrap();
      if (pnlData?.[0]) {
        const enterRow = tableRef.current.getRow(
          pnlData[0].enter_trade_history_uuid
        );
        const exitRow = tableRef.current.getRow(
          pnlData[0].exit_trade_history_uuid
        );
        if (enterRow && exitRow) {
          enterRow.toggleExpanded(true);
          setSelectedTradeHistoryPair({
            enter: enterRow?.original.uuid,
            exit: exitRow?.original.uuid,
          });
        }
      }
      setPnlTableData(
        orderBy(
          pnlData || [],
          (o) => DateTime.fromISO(o.registered_datetime).toMillis(),
          'desc'
        ).map((item) => ({
          ...item,
          datetime: item.registered_datetime,
          ...(isMobile
            ? {
                uuid: truncate(item.uuid, { length: 10 }),
                trade_uuid: truncate(item.trade_uuid, { length: 10 }),
                enter_trade_history_uuid: truncate(
                  item.enter_trade_history_uuid,
                  { length: 10 }
                ),
                exit_trade_history_uuid: truncate(
                  item.exit_trade_history_uuid,
                  { length: 10 }
                ),
              }
            : {}),
        }))
      );
    } catch {
      setPnlTableData([]);
    }
  };

  useEffect(() => {
    tableRef.current.toggleAllRowsExpanded(false);
    setSelectedUuid({});
  }, [uuid]);

  useEffect(() => {
    if (withPnlHistory) {
      tableRef.current.toggleAllRowsExpanded(false);
      setSelectedTradeHistoryPair();
    }
  }, [pagination, withPnlHistory]);

  const getRowId = useCallback((row) => row.uuid, []);
  const onUuidClick = useCallback(({ row, column, cell }) => {
    if (!row) setSelectedUuid({});
    else {
      if (!row.getIsExpanded()) row.toggleExpanded(true);
      setSelectedUuid({ [column.id]: cell.getValue() });
    }
  }, []);

  const renderSubComponent = useCallback(
    ({ row, meta }) => {
      if (withOrderHistory) {
        const [[_, orderUuid]] = Object.entries(meta.selectedUuid);
        return (
          <Box
            className="animate__animated animate__fadeIn"
            sx={{
              p: 1,
              textAlign: 'center',
            }}
          >
            <Typography gutterBottom variant="h6" sx={{ fontWeight: 700 }}>
              {t('Order History')}
            </Typography>
            <OrderHistoryTable
              uuid={orderUuid}
              tradeConfigUuid={row.original.trade_config_uuid}
            />
          </Box>
        );
      }

      return (
        <Box
          className="animate__animated animate__fadeIn"
          sx={{
            bgcolor: alpha(theme.palette.primary.main, 0.1),
            p: 1,
            textAlign: 'center',
          }}
        >
          <Typography gutterBottom variant="h6" sx={{ fontWeight: 700 }}>
            {t('PnL History')}
          </Typography>
          <ReactTableUI
            columns={pnlColumns}
            data={pnlTableData}
            noDisplayMessage={t('There are no linked revenue statistics')}
          />
        </Box>
      );
    },
    [pnlColumns, pnlTableData, withPnlHistory, withOrderHistory]
  );

  return (
    <ReactTableUI
      enableTablePaginationUI={withPnlHistory}
      ref={tableRef}
      columns={columns}
      data={tableData}
      options={{
        getRowId,
        state: { expanded, pagination },
        onExpandedChange: (newExpanded) =>
          setExpanded((isFunction(newExpanded) ? newExpanded() : null) || {}),
        onPaginationChange: setPagination,
        meta: {
          marketCodes,
          onUuidClick,
          selectedUuid,
          selectedTradeHistoryPair,
          expandIcon: ExpandMoreIcon,
        },
      }}
      renderSubComponent={renderSubComponent}
      getCellProps={() => ({ onClick: () => {}, sx: { height: 40 } })}
      getRowProps={(row, { table }) => ({
        onClick: () => {
          if (withPnlHistory) handleGetPnlHistory(row);
        },
        sx: {
          cursor: withPnlHistory ? 'pointer' : undefined,
          bgcolor:
            withPnlHistory && row.index === 0
              ? row.original.bgcolor
              : undefined,
          ...(!row.getIsExpanded() &&
          table.getIsSomeRowsExpanded() &&
          row.id !== selectedTradeHistoryPair?.enter &&
          row.id !== selectedTradeHistoryPair?.exit
            ? { opacity: 0.2 }
            : {}),
          ...(row.getIsExpanded() ||
          row.id === selectedTradeHistoryPair?.enter ||
          row.id === selectedTradeHistoryPair?.exit
            ? { bgcolor: alpha(theme.palette.primary.main, 0.15) }
            : {}),
        },
      })}
      getTableProps={() => ({ sx: { fontSize: '0.9em' } })}
      showProgressBar={isFetching || isFetchingByUuid}
      isLoading={isFetching || isFetchingByUuid}
    />
  );
}
