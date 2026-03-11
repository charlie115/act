import React, { useCallback, useMemo, useState, useEffect, useRef } from 'react';

import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

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

import renderTradeCapitalCell from 'components/tables/trigger/renderTransactionAmountCell';
import renderValueCell from 'components/tables/trigger/renderValueCell';

import BlockIcon from '@mui/icons-material/Block';

export default function PnLHistoryTable({
  marketCodeCombination,
  tradeConfigUuid,
  tradeUuid,
}) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const tableRef = useRef();

  const { i18n, t } = useTranslation();

  const [expanded, setExpanded] = useState({});
  const [selectedUuid, setSelectedUuid] = useState({});
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 10 });
  
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

  // Prepare sorted table data first (without base assets)
  const sortedTableData = useMemo(
    () => {
      if (!data) return [];
      
      return orderBy(
        data,
        (o) => o.registered_datetime,
        'desc'
      );
    },
    [data]
  );

  // Get currently visible rows based on pagination
  const visibleRows = useMemo(() => {
    const startIndex = pagination.pageIndex * pagination.pageSize;
    const endIndex = startIndex + pagination.pageSize;
    return sortedTableData.slice(startIndex, endIndex);
  }, [sortedTableData, pagination.pageIndex, pagination.pageSize]);

  // Fetch base assets only for currently visible rows
  useEffect(() => {
    if (!visibleRows.length) return;

    // Get trades that need to be processed from visible rows only
    const tradesToProcess = visibleRows.filter((item) => (
      item.trade_uuid && 
      !processedTrades[item.trade_uuid] && 
      !baseAssetMap[item.trade_uuid]
    ));

    // Process trades one by one to avoid overwhelming the API
    if (tradesToProcess.length > 0) {
      const tradeToProcess = tradesToProcess[0];
      
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
        .catch((_error) => {
          // Silently handle error and mark as error state
          setProcessedTrades((prev) => ({
            ...prev,
            [tradeToProcess.trade_uuid]: 'error'
          }));
        });
    }
  }, [visibleRows, baseAssetMap, processedTrades, getTradeLog, tradeConfigUuid]);

  // Final table data - keep this stable to prevent page resets
  const tableData = useMemo(
    () => sortedTableData.map((item) => ({
        ...item,
        datetime: item.registered_datetime,
        // Don't include baseAsset, name, or icon here to keep data stable
      })),
    [sortedTableData] // Only depend on sortedTableData, not baseAssetMap
  );

  // Custom cell renderer for base asset that looks up dynamically
  const renderBaseAssetCell = useCallback(({ row }) => {
    const baseAsset = baseAssetMap[row.original.trade_uuid] || '';
    return baseAsset || ''; // Return empty string if not loaded yet
  }, [baseAssetMap]);

  // Custom cell renderer for asset icon that looks up dynamically  
  const renderAssetIconCellDynamic = useCallback(({ row, table: _table }) => {
    const baseAsset = baseAssetMap[row.original.trade_uuid] || '';
    const icon = baseAsset && assetsData ? assetsData[baseAsset]?.icon : null;
    
    // Implement the same logic as renderAssetIconCell directly
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          textAlign: 'center',
        }}
      >
        {icon ? (
          <Box
            component="img"
            loading="lazy"
            src={icon}
            alt=""
            sx={{ width: isMobile ? '0.7rem' : 20 }}
          />
        ) : (
          <BlockIcon color="secondary" sx={{ fontSize: isMobile ? '0.7rem' : 20 }} />
        )}
      </Box>
    );
  }, [baseAssetMap, assetsData, isMobile]);

  const columns = useMemo(
    () => [
      {
        accessorKey: 'icon',
        enableGlobalFilter: false,
        enableSorting: false,
        size: 5,
        header: <span />,
        cell: renderAssetIconCellDynamic,
      },
      {
        accessorKey: 'baseAsset',
        size: isMobile ? 25 : 45,
        header: t('Base Asset'),
        cell: renderBaseAssetCell,
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
    [i18n.language, isMobile, t, renderAssetIconCellDynamic, renderBaseAssetCell]
  );

  // Filter out columns that should be hidden on mobile
  const visibleColumns = useMemo(() => (
    columns.filter((column) => !(isMobile && column.hidden))
  ), [columns, isMobile]);

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
            sx={{ bgcolor: alpha(theme.palette.primary?.main || '#007cff', 0.05) }}
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
          sx={{ bgcolor: alpha(theme.palette.primary?.main || '#007cff', 0.05) }}
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
      ref={tableRef}
      columns={visibleColumns}
      data={tableData}
      options={{
        getRowId,
        state: { expanded, pagination },
        onExpandedChange: (newExpanded) => setExpanded(newExpanded() || {}),
        onPaginationChange: setPagination,
        meta: {
          isMobile,
          onUuidClick,
          selectedUuid,
          expandIcon: ExpandMoreIcon,
        },
      }}
      renderSubComponent={renderSubComponent}
      getHeaderProps={() => ({
        sx: {
          bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.100',
          fontSize: isMobile ? '0.6em' : '0.7em',
          textAlign: isMobile ? 'center' : 'left',
          padding: isMobile ? theme.spacing(0.5, 0.2) : theme.spacing(1, 1.5),
          whiteSpace: isMobile ? 'normal' : 'normal',
          overflow: 'visible',
          textOverflow: 'clip',
          lineHeight: isMobile ? 1.2 : 1.5,
          wordBreak: isMobile ? 'break-word' : 'normal',
        },
      })}
      getCellProps={() => ({ sx: { height: 40 } })}
      getRowProps={(row, { table }) => ({
        sx: {
          ...(row.getIsExpanded()
            ? { bgcolor: alpha(theme.palette.primary?.main || '#007cff', 0.05) }
            : {}),
          ...(!row.getIsExpanded() && table.getIsSomeRowsExpanded()
            ? { opacity: 0.2 }
            : {}),
        },
      })}
      getTableProps={() => ({
        sx: {
          border: 1,
          borderColor: 'divider',
          fontSize: isMobile ? '0.65em' : '1.15em',
        },
      })}
      showProgressBar={isFetching}
      isLoading={isFetching}
    />
  );
}
