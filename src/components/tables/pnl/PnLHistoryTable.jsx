import React, { useCallback, useMemo, useState, useEffect } from 'react';

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
  // useGetTradeByUuidQuery,
  useGetTradeLogByUuidQuery,
  useLazyGetTradeLogByUuidQuery,
} from 'redux/api/drf/tradecore';

import orderBy from 'lodash/orderBy';

import ReactTableUI from 'components/ReactTableUI';

import TradeHistoryTable from 'components/tables/trade_history/TradeHistoryTable';

import renderAssetIconCell from 'components/tables/common/renderAssetIconCell';
import renderColoredSignedNumberCell from 'components/tables/common/renderColoredSignedNumberCell';
import renderDateCell from 'components/tables/common/renderDateCell';
import renderExpandCell from 'components/tables/common/renderExpandCell';
import renderUuidCell from 'components/tables/common/renderUuidCell';
import renderCheckbox from 'components/tables/trigger/renderCheckbox';

import renderMarketCodesCell from 'components/tables/trigger/renderMarketCodesCell';
import renderTradeCapitalCell from 'components/tables/trigger/renderTransactionAmountCell';
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
  
  // Get PnL history data
  const { data, isFetching } = useGetPnlHistoryQuery({
    tradeConfigUuid,
    tradeUuid,
  });

  const { data: assetsData } = useGetAssetsQuery();

  // Selected trade data for expanded view
  const { data: selectedTradeData } = useGetTradeLogByUuidQuery(
    {
      tradeConfigUuid,
      uuid: selectedUuid.trade_uuid,
    },
    { skip: !selectedUuid?.trade_uuid }
  );

  // Store base asset data for PnL entries
  const [baseAssetMap, setBaseAssetMap] = useState({});
  
  // Get a function to trigger trade log queries on demand
  const [getTradeLog] = useLazyGetTradeLogByUuidQuery();

  // Track which trade UUIDs we've processed
  const [processedTrades, setProcessedTrades] = useState({});

  // Fetch trade logs when PnL data changes
  useEffect(() => {
    if (!data) return;

    // Get trades that need to be processed
    const tradesToProcess = data.filter((item) => (
      item.trade_uuid && 
      !processedTrades[item.trade_uuid] && 
      !baseAssetMap[item.trade_uuid]
    ));

    // Sort by datetime descending to process newest first
    const sortedTrades = orderBy(
      tradesToProcess,
      (item) => item.registered_datetime,
      'desc'
    );

    // Process the first unprocessed trade
    if (sortedTrades.length > 0) {
      const tradeToProcess = sortedTrades[0];
      
      // Mark as being processed
      setProcessedTrades((prev) => ({
        ...prev,
        [tradeToProcess.trade_uuid]: 'processing'
      }));

      // Fetch trade log data
      getTradeLog({
        tradeConfigUuid,
        uuid: tradeToProcess.trade_uuid
      }).unwrap()
        .then((result) => {
          if (result && result.base_asset) {
            // Update base asset map with the result
            setBaseAssetMap((prev) => ({
              ...prev,
              [tradeToProcess.trade_uuid]: result.base_asset
            }));
          }
          
          // Mark as processed
          setProcessedTrades((prev) => ({
            ...prev,
            [tradeToProcess.trade_uuid]: 'complete'
          }));
        })
        .catch((error) => {
          console.error('Error fetching trade log:', error);
          setProcessedTrades((prev) => ({
            ...prev,
            [tradeToProcess.trade_uuid]: 'error'
          }));
        });
    }
  }, [data, baseAssetMap, processedTrades, getTradeLog, tradeConfigUuid]);

  const columns = useMemo(
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
        size: isMobile ? 25 : 45,
        header: t('Base Asset'),
      },
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
        enableHiding: true,
        hidden: isMobile,
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
        accessorKey: 'more_info',
        enableGlobalFilter: false,
        enableSorting: false,
        size: 11,
        maxSize: 11,
        cell: renderExpandCell,
        header: <span />,
      },
    ],
    [i18n.language, isMobile, t]
  );

  // Filter out columns that should be hidden on mobile
  const visibleColumns = useMemo(() => (
    columns.filter((column) => !(isMobile && column.hidden))
  ), [columns, isMobile]);

  const tableData = useMemo(
    () => {
      if (!data) return [];
      
      return orderBy(
        data,
        (o) => o.registered_datetime,
        'desc'
      ).map((item) => {
        const baseAsset = baseAssetMap[item.trade_uuid] || '';
        
        return {
          ...item,
          datetime: item.registered_datetime,
          baseAsset,
          name: baseAsset,
          icon: baseAsset && assetsData ? assetsData[baseAsset]?.icon : null,
        };
      });
    },
    [data, baseAssetMap, assetsData]
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
        size: isMobile ? 25 : 45,
        header: t('Base Asset'),
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
        accessorKey: 'tradeCapital',
        size: isMobile ? 25 : 120,
        header: t('Trade Capital'),
        cell: renderTradeCapitalCell,
      },
      {
        accessorKey: 'deleted',
        size: isMobile ? 25 : 140,
        header: t('Deleted'),
        cell: renderCheckbox,
        props: {
          sx: { textAlign: 'center' },
        }
      },
      {
        accessorKey: 'created',
        header: t('Created'),
        size: isMobile ? 40 : 140,
        cell: renderDateCell,
      },
    ],
    [i18n.language, isMobile, t]
  );
  
  const tradeTableData = useMemo(() => {
    if (!selectedTradeData) return [];
    return [
      {
        ...selectedTradeData,
        baseAsset: selectedTradeData.base_asset,
        name: selectedTradeData.base_asset,
        entry: selectedTradeData.low,
        exit: selectedTradeData.high,
        tradeCapital: selectedTradeData.trade_capital,
        created: selectedTradeData.registered_datetime,
        isTether: selectedTradeData.usdt_conversion,
        deleted: selectedTradeData.deleted,
        marketCodes: {
          targetMarketCode: marketCodeCombination?.target?.value || '',
          originMarketCode: marketCodeCombination?.origin?.value || '',
        },
        icon: selectedTradeData.base_asset && assetsData 
          ? assetsData[selectedTradeData.base_asset]?.icon 
          : null,
      },
    ];
  }, [selectedTradeData, assetsData, marketCodeCombination]);

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
      const [target, origin] = (row.original.market_code_combination || '').split(':');
      const marketCodes = {
        targetMarketCode: target || '',
        originMarketCode: origin || '',
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
    [t, theme, tradeColumns, tradeTableData]
  );

  return (
    <ReactTableUI
      enableTablePaginationUI
      columns={visibleColumns}
      data={tableData}
      options={{
        getRowId,
        state: { expanded },
        onExpandedChange: (newExpanded) => setExpanded(newExpanded() || {}),
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
