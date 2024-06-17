import React, { useCallback, useMemo, useState } from 'react';

import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import SyncAltIcon from '@mui/icons-material/SyncAlt';

import useMediaQuery from '@mui/material/useMediaQuery';
import { alpha, useTheme } from '@mui/material/styles';

import { useTranslation } from 'react-i18next';

import { useGetAssetsQuery } from 'redux/api/drf/infocore';
import {
  useGetPnlHistoryQuery,
  useGetTradeByUuidQuery,
} from 'redux/api/drf/tradecore';

import { DateTime } from 'luxon';

import orderBy from 'lodash/orderBy';

import ReactTableUI from 'components/ReactTableUI';

import TradeHistoryTable from 'components/tables/trade_history/TradeHistoryTable';

import renderAssetIconCell from 'components/tables/common/renderAssetIconCell';
import renderColoredSignedNumberCell from 'components/tables/common/renderColoredSignedNumberCell';
import renderDateCell from 'components/tables/common/renderDateCell';
import renderExpandCell from 'components/tables/common/renderExpandCell';
import renderUuidCell from 'components/tables/common/renderUuidCell';

import renderMarketCodesCell from 'components/tables/trigger/renderMarketCodesCell';
import renderStatusCell from 'components/tables/trigger/renderStatusCell';
import renderValueCell from 'components/tables/trigger/renderValueCell';

export default function PnLHistoryTable({
  marketCodeCombination,
  tradeConfigUuid,
  tradeUuid,
}) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const { i18n, t } = useTranslation();

  const [expanded, setExpanded] = useState({});

  const [selectedUuid, setSelectedUuid] = useState({});
  const { data, isFetching } = useGetPnlHistoryQuery({
    tradeConfigUuid,
    tradeUuid,
  });
  const { data: tradeData } = useGetTradeByUuidQuery(
    {
      tradeConfigUuid,
      uuid: selectedUuid.trade_uuid,
    },
    { skip: !selectedUuid?.trade_uuid }
  );

  const { data: assetsData } = useGetAssetsQuery();

  const columns = useMemo(
    () => [
      {
        accessorKey: 'datetime',
        size: isMobile ? 30 : 100,
        header: t('Transaction Date'),
        cell: renderDateCell,
      },
      {
        accessorKey: 'uuid',
        size: isMobile ? 40 : 120,
        header: t('ID'),
      },
      {
        accessorKey: 'trade_uuid',
        size: isMobile ? 40 : 120,
        header: t('Trade ID'),
        cell: renderUuidCell,
      },
      {
        accessorKey: 'enter_trade_history_uuid',
        size: isMobile ? 40 : 120,
        header: t('Enter Trade History ID'),
        cell: renderUuidCell,
      },
      {
        accessorKey: 'exit_trade_history_uuid',
        size: isMobile ? 40 : 120,
        header: t('Exit Trade History ID'),
        cell: renderUuidCell,
      },
      {
        accessorKey: 'realized_premium_gap_p',
        size: isMobile ? 30 : 80,
        header: t('Realized Premium Gap (%)'),
        cell: renderColoredSignedNumberCell,
      },
      {
        accessorKey: 'total_currency',
        size: isMobile ? 30 : 80,
        header: t('Total Currency'),
      },
      {
        accessorKey: 'total_pnl',
        size: isMobile ? 30 : 80,
        header: t('Total PnL'),
        cell: renderColoredSignedNumberCell,
      },
      {
        accessorKey: 'total_pnl_after_fee',
        size: isMobile ? 30 : 80,
        header: t('Total PnL After Fee'),
        cell: renderColoredSignedNumberCell,
      },
      {
        accessorKey: 'total_pnl_after_fee_kimp',
        size: isMobile ? 30 : 80,
        header: t('Total PnL After Fee KIMP'),
      },
      {
        accessorKey: 'more_info',
        enableGlobalFilter: false,
        enableSorting: false,
        size: 11,
        maxSize: 11,
        cell: renderExpandCell,
        header: <span />,
      },
    ],
    [i18n.language, isMobile]
  );

  const tableData = useMemo(
    () =>
      orderBy(
        data || [],
        (o) =>
          DateTime.fromISO(o.registered_datetime, {
            zone: 'UTC',
          }).toMillis(),
        'desc'
      ).map((item) => ({
        ...item,
        datetime: item.registered_datetime,
      })),
    [data]
  );

  const tradeColumns = useMemo(
    () => [
      {
        accessorKey: 'icon',
        enableGlobalFilter: false,
        enableSorting: false,
        size: 5,
        header: <span />,
        cell: renderAssetIconCell,
      },
      {
        accessorKey: 'baseAsset',
        size: isMobile ? 25 : 50,
        header: t('Base Asset'),
      },
      {
        accessorKey: 'marketCodes',
        enableGlobalFilter: false,
        enableSorting: false,
        size: isMobile ? 65 : 180,
        header: <SyncAltIcon />,
        cell: renderMarketCodesCell,
      },
      {
        accessorKey: 'entry',
        size: isMobile ? 25 : 120,
        header: t('Entry'),
        cell: renderValueCell,
      },
      {
        accessorKey: 'exit',
        size: isMobile ? 25 : 120,
        header: t('Exit'),
        cell: renderValueCell,
      },
      {
        accessorKey: 'status',
        size: isMobile ? 25 : 140,
        header: t('Status'),
        cell: renderStatusCell,
      },
      {
        accessorKey: 'created',
        header: t('Created'),
        size: isMobile ? 40 : 140,
      },
    ],
    [i18n.language, isMobile]
  );
  const tradeTableData = useMemo(() => {
    if (!tradeData) return [];
    return [
      {
        ...tradeData,
        baseAsset: tradeData.base_asset,
        name: tradeData.base_asset,
        entry: tradeData.low,
        exit: tradeData.high,
        created: DateTime.fromISO(tradeData.registered_datetime).toLocaleString(
          DateTime.DATETIME_MED
        ),
        isTether: tradeData.usdt_conversion,
        status: tradeData.trigger_switch,
        marketCodes: {
          targetMarketCode: marketCodeCombination.target.value,
          originMarketCode: marketCodeCombination.origin.value,
        },
        icon: assetsData?.[tradeData.base_asset]?.icon,
      },
    ];
  }, [tradeData, assetsData, marketCodeCombination]);

  const getRowId = useCallback((row) => row.uuid, []);
  const onUuidClick = useCallback(({ row, column, cell }) => {
    if (!row) {
      setSelectedUuid({});
    } else {
      if (!row.getIsExpanded()) row.toggleExpanded(true);
      setSelectedUuid({
        [column.id]: cell.getValue(),
      });
    }
  }, []);

  const renderSubComponent = useCallback(
    ({ row, meta }) => {
      const [target, origin] = row.original.market_code_combination.split(':');
      const marketCodes = {
        targetMarketCode: target,
        originMarketCode: origin,
      };

      const [[key, uuid]] = Object.entries(meta.selectedUuid);

      if (key === 'trade_uuid')
        return (
          <Box
            className="animate__animated animate__fadeIn"
            sx={{ bgcolor: alpha(theme.palette.primary.main, 0.05) }}
          >
            <Box sx={{ p: 1, textAlign: 'center' }}>
              <Typography gutterBottom variant="h6" sx={{ fontWeight: 700 }}>
                {t('Trade')}
              </Typography>
              <ReactTableUI
                columns={tradeColumns}
                data={tradeTableData}
                getTableProps={() => ({ sx: { fontSize: '1em' } })}
              />
            </Box>
          </Box>
        );
      return (
        <Box
          className="animate__animated animate__fadeIn"
          sx={{ bgcolor: alpha(theme.palette.primary.main, 0.05) }}
        >
          <Box sx={{ p: 1, textAlign: 'center' }}>
            <Typography gutterBottom variant="h6" sx={{ fontWeight: 700 }}>
              {t('Trade History')}
            </Typography>
            <TradeHistoryTable
              withOrderHistory
              marketCodes={marketCodes}
              uuid={uuid}
              tradeConfigUuid={row.original.trade_config_uuid}
            />
          </Box>
        </Box>
      );
    },
    [tradeColumns, tradeTableData]
  );

  return (
    <ReactTableUI
      enableTablePaginationUI
      // ref={tableRef}
      columns={columns}
      data={tableData}
      options={{
        getRowId,
        state: { expanded },
        onExpandedChange: (newExpanded) => setExpanded(newExpanded() || {}),
        //   onPaginationChange: setPagination,
        meta: {
          isMobile,
          onUuidClick,
          selectedUuid,
          expandIcon: ExpandMoreIcon,
        },
      }}
      renderSubComponent={renderSubComponent}
      getCellProps={() => ({ sx: { height: 40 } })}
      getRowProps={(row, { table }) => ({
        sx: {
          ...(row.getIsExpanded()
            ? { bgcolor: alpha(theme.palette.primary.main, 0.05) }
            : {}),
          ...(!row.getIsExpanded() && table.getIsSomeRowsExpanded()
            ? { opacity: 0.2 }
            : {}),
        },
      })}
      showProgressBar={isFetching}
      isLoading={isFetching}
    />
  );
}
