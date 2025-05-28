import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import ExitToAppIcon from '@mui/icons-material/ExitToApp';
import SyncAltIcon from '@mui/icons-material/SyncAlt';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';

import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import { useTranslation } from 'react-i18next';

import {
  useGetAssetsQuery,
  useGetFundingRateByMarketCodeQuery,
} from 'redux/api/drf/infocore';
import {
  useDeleteMultipleTradesMutation,
  useDeleteRepeatTradeMutation,
  useGetAllRepeatTradesQuery,
  useGetAllTradesQuery,
  useGetTradesByTradeConfigQuery,
  useGetTradeHistoryQuery,
  useExitMultipleTradesMutation,
} from 'redux/api/drf/tradecore';

import { useSelector } from 'react-redux';

import isFunction from 'lodash/isFunction';

import isKoreanMarket from 'utils/isKoreanMarket';
import formatIntlNumber from 'utils/formatIntlNumber';

import AssetSearchInput from 'components/AssetSearchInput';
import AssetTradeConfig from 'components/AssetTradeConfig';
import AutoRepeatForm from 'components/AutoRepeatForm';
import DeleteAlert from 'components/DeleteAlert';
import ExitTradeAlert from 'components/ExitTradeAlert';
import DropdownMenu from 'components/DropdownMenu';
import PremiumDataChartViewer from 'components/PremiumDataChartViewer';
import ReactTableUI from 'components/ReactTableUI';
import UpdateTriggerForm from 'components/UpdateTriggerForm';

import { TRIGGER_LIST } from 'constants/lists';

import TradeHistoryTable from 'components/tables/trade_history/TradeHistoryTable';

import renderAssetIconCell from 'components/tables/common/renderAssetIconCell';
import renderCurrencyFormatCell from 'components/tables/common/renderCurrencyFormatCell';
import renderExpandCell from 'components/tables/common/renderExpandCell';
import renderFundingRateHeader from 'components/tables/common/renderFundingRateHeader';
import renderFundingRateCell from 'components/tables/common/renderFundingRateCell';
import renderDateCell from 'components/tables/common/renderDateCell';

import renderAutoRepeatSwitchCell from './renderAutoRepeatSwitchCell';
import renderMarketCodesCell from './renderMarketCodesCell';
import renderSelectCell from './renderSelectCell';
import renderStatusCell from './renderStatusCell';
import renderValueCell from './renderValueCell';

import renderSelectHeader from './renderSelectHeader';

export default function TriggersTable({
  marketCodeCombination,
  queryKey,
  tradeConfigAllocations,
  tradeConfigUuids,
  triggerScannerUuid,
  scannerTradeConfigUuid,
}) {
  const assetSearchRef = useRef();
  const premiumDataViewerRef = useRef();
  const tableRef = useRef();

  const { i18n, t } = useTranslation();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const { user } = useSelector((state) => state.auth);

  const [expanded, setExpanded] = useState({});
  const [globalFilter, setGlobalFilter] = useState('');
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 100 });
  const [rowSelection, setRowSelection] = useState({});

  const [autoRepeatTrade, setAutoRepeatTrade] = useState();

  const [assetsByMarketCode, setAssetsByMarketCode] = useState();

  const [selectedAsset, setSelectedAsset] = useState('');

  const [deleteAlert, setDeleteAlert] = useState(false);

  const [exitTradeAlert, setExitTradeAlert] = useState(false);

  const [triggerConfig, setTriggerConfig] = useState();

  const [triggerTypeList, setTriggerTypeList] = useState([]);
  const [selectedTriggerType, setSelectedTriggerType] = useState();

  const [selectedTrade, setSelectedTrade] = useState();
  const [displayTradeHistory, setDisplayTradeHistory] = useState(false);

  const [klineInterval, setKlineInterval] = useState('1T');

  const betweenFutures = marketCodeCombination?.target && marketCodeCombination?.origin 
    ? !marketCodeCombination.target.isSpot && !marketCodeCombination.origin.isSpot 
    : false;

  // Conditional query based on whether we're in scanner context or not
  const allTradesQuery = useGetAllTradesQuery(
    { 
      tradeConfigUuids,
    },
    { pollingInterval: 1000 * 1, skip: !!autoRepeatTrade || !!triggerScannerUuid }
  );

  const scannerTradesQuery = useGetTradesByTradeConfigQuery(
    { 
      tradeConfigUuid: scannerTradeConfigUuid,
      trigger_scanner_uuid: triggerScannerUuid,
    },
    { pollingInterval: 1000 * 1, skip: !!autoRepeatTrade || !triggerScannerUuid }
  );

  // Use the appropriate query result
  const { data, isLoading, isSuccess } = triggerScannerUuid ? scannerTradesQuery : allTradesQuery;

  const { data: repeatTrades } = useGetAllRepeatTradesQuery({
    tradeConfigUuids,
  });

  const [deleteRepeatTrade] = useDeleteRepeatTradeMutation();

  const [
    deleteMultipleTrades,
    { isLoading: isDeleteLoading, isSuccess: isDeleteSuccess },
  ] = useDeleteMultipleTradesMutation();

  const [ 
    exitMultipleTrades, 
    { isLoading: isExitTradeLoading, isSuccess: isExitTradeSuccess }
   ] = useExitMultipleTradesMutation();

  const { data: tradeHistoryData } = useGetTradeHistoryQuery(
    {
      tradeConfigUuid: selectedTrade?.trade_config_uuid,
      tradeUuid: selectedTrade?.uuid,
    },
    { skip: !selectedTrade }
  );

  const { data: fundingRate } = useGetFundingRateByMarketCodeQuery(
    { assetsByMarketCode },
    {
      pollingInterval: 1000 * 60,
      skip: !assetsByMarketCode,
    }
  );

  const { data: assetsData } = useGetAssetsQuery();

  const marketCodes = useMemo(() => {
    if (!marketCodeCombination?.value || marketCodeCombination?.value === 'ALL')
      return null;
    return {
      targetMarketCode: marketCodeCombination?.target?.value,
      originMarketCode: marketCodeCombination?.origin?.value,
    };
  }, [marketCodeCombination?.value]);

  const tradeConfigAllocation = useMemo(
    () =>
      user?.trade_config_allocations?.find(
        (o) =>
          o.target_market_code === marketCodes?.targetMarketCode &&
          o.origin_market_code === marketCodes?.originMarketCode
      ),
    [marketCodes, user?.trade_config_allocations]
  );

  useEffect(() => {
    if (isSuccess && data?.length > 0) {
      const byMarketCodeAssets = {};
      data
        .filter((datum) => datum.trade_capital !== null)
        .forEach((datum) => {
          const tradeConfig = tradeConfigAllocations.find(
            (o) => o.uuid === datum.trade_config_uuid
          );
          if (!tradeConfig?.target?.value?.includes('SPOT')) {
            if (!byMarketCodeAssets[tradeConfig.target.value])
              byMarketCodeAssets[tradeConfig.target.value] = {};
            byMarketCodeAssets[tradeConfig.target.value][
              datum.base_asset
            ] = true;
          }
          if (!tradeConfig?.origin?.value?.includes('SPOT')) {
            if (!byMarketCodeAssets[tradeConfig.origin.value])
              byMarketCodeAssets[tradeConfig.origin.value] = {};
            byMarketCodeAssets[tradeConfig.origin.value][
              datum.base_asset
            ] = true;
          }
        });
      setAssetsByMarketCode(byMarketCodeAssets);
    }
  }, [data, isSuccess, tradeConfigAllocations]);

  useEffect(() => {
    if (isDeleteSuccess) {
      tableRef.current?.toggleAllRowsSelected(false);
      setDeleteAlert(false);
    }
  }, [isDeleteSuccess]);

  useEffect(() => {
    if (isExitTradeSuccess) {
      tableRef.current?.toggleAllRowsSelected(false);
      setExitTradeAlert(false);
    }
  }, [isExitTradeSuccess]);

  useEffect(() => {
    const triggers = TRIGGER_LIST.map((trigger) => ({
      label: trigger.getLabel(),
      value: trigger.value,
      icon: <trigger.icon />,
    }));
    setTriggerTypeList(triggers);
    if (!selectedTriggerType) setSelectedTriggerType(triggers[0]);
  }, [selectedTriggerType, i18n.language]);

  const columns = useMemo(
    () => [
      ...(!triggerScannerUuid ? [{
        accessorKey: 'select',
        enableGlobalFilter: false,
        enableSorting: false,
        size: isMobile ? 15 : 30,
        header: renderSelectHeader,
        cell: renderSelectCell,
      }] : []),
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
        size: isMobile ? 40 : 70,
        header: <SyncAltIcon sx={{ fontSize: isMobile ? '0.8rem' : '1rem' }} />,
        cell: renderMarketCodesCell,
        props: { sx: { textAlign: 'center' } },
      },
      {
        accessorKey: 'entry',
        size: isMobile ? 27 : 80,
        header: betweenFutures ? t('Low Value') : t('Entry'),
        cell: renderValueCell,
      },
      {
        accessorKey: 'exit',
        size: isMobile ? 27 : 80,
        header: betweenFutures ? t('High Value') : t('Exit'),
        cell: renderValueCell,
      },
      {
        accessorKey: 'tradeCapital',
        size: isMobile ? 29 : 80,
        header: t('Trade Capital'),
        cell: renderCurrencyFormatCell,
      },
      {
        accessorKey: 'status',
        size: isMobile ? 30 : 65,
        header: t('Status'),
        cell: renderStatusCell,
      },
      ...(marketCodeCombination?.value === 'ALL' && !isMobile
        ? [
            {
              accessorKey: 'targetFundingRate',
              header: t('Funding Rate'),
              size: isMobile ? 25 : 85,
              cell: renderFundingRateCell,
            },
            {
              accessorKey: 'originFundingRate',
              header: t('Funding Rate'),
              size: isMobile ? 25 : 85,
              cell: renderFundingRateCell,
            },
          ]
        : []),
      ...(marketCodeCombination?.target &&
      !marketCodeCombination?.target?.isSpot &&
      !isMobile
        ? [
            {
              accessorKey: 'targetFundingRate',
              header: renderFundingRateHeader,
              cell: renderFundingRateCell,
              size: isMobile ? 25 : 85,
            },
          ]
        : []),
      ...(marketCodeCombination?.origin &&
      !marketCodeCombination?.origin?.isSpot &&
      !isMobile
        ? [
            {
              accessorKey: 'originFundingRate',
              header: renderFundingRateHeader,
              cell: renderFundingRateCell,
              size: isMobile ? 25 : 85,
            },
          ]
        : []),
      {
        accessorKey: 'autoRepeatStatus',
        size: isMobile ? 25 : 60,
        header: t('Repeat Transaction Status'),
      },
      {
        accessorKey: 'autoRepeatSwitch',
        size: isMobile ? 35 : 60,
        header: t('Auto Repeat'),
        cell: renderAutoRepeatSwitchCell,
        props: { sx: { textAlign: 'center' } },
      },
      {
        accessorKey: 'created',
        size: isMobile ? 30 : 100,
        header: t('Created'),
        cell: renderDateCell,
      },
      {
        accessorKey: 'edit',
        enableGlobalFilter: false,
        enableSorting: false,
        size: 20,
        maxSize: 20,
        cell: renderExpandCell,
        header: <span />,
      },
    ],
    [marketCodeCombination, i18n.language, isMobile, triggerScannerUuid]
  );

  const tableData = useMemo(() => {
    if (!data) return [];
    if (selectedAsset && !triggerScannerUuid) {
      // --- Add Row Configuration ---
      // Still extract from element.props.src for the Add row, as this works
      const targetIconElement = marketCodeCombination?.target?.icon;
      const originIconElement = marketCodeCombination?.origin?.icon;
      const targetIconUrl = targetIconElement?.props?.src;
      const originIconUrl = originIconElement?.props?.src;

      return [
        {
          uuid: `add-${selectedAsset}`,
          add: true,
          baseAsset: selectedAsset,
          name: selectedAsset,
          icon: assetsData?.[selectedAsset]?.icon,
          marketCodes: {
            targetMarketCode: marketCodeCombination?.target?.value,
            originMarketCode: marketCodeCombination?.origin?.value,
          },
          targetMarketIcon: targetIconUrl, // Use extracted URL
          originMarketIcon: originIconUrl, // Use extracted URL
          status: null,
          entry: null,
          exit: null,
          tradeCapital: null,
          created: null,
          autoRepeatSwitch: null,
          autoRepeatStatus: '-',
          isTether: null,
          targetFundingRate: null,
          originFundingRate: null,
        },
      ];
    }

    // --- Existing Row Mapping Logic ---
    return data
      ?.filter((item) => {
        if (!item) return false;

        // 1. Check if the item matches the selected market code combination
        const marketMatch = !marketCodeCombination || marketCodeCombination.value === 'ALL' || 
                            marketCodeCombination?.tradeConfigUuid === item.trade_config_uuid;
        
        // If the market doesn't match, filter out this item immediately
        if (!marketMatch) {
          return false;
        }

        // 2. If market matches, THEN filter by selected trigger type (if not 'ALL')
        if (!selectedTriggerType || selectedTriggerType.value === 'ALL') {
          return true; // Keep item if type filter is 'ALL'
        } 

        // If type is 'alarms', check the trade_capital
        if (selectedTriggerType.value === 'alarms') {
          return item.trade_capital === null; // Keep item if it's an Alarm
        } 
        
        // Otherwise (type must be 'autoTrade'), check the trade_capital
        return item.trade_capital !== null; // Keep item if it's an Auto Trade
      })
      .map((trade) => {
        const tradeConfig = tradeConfigAllocations.find(
          (o) => o.uuid === trade.trade_config_uuid
        );
        if (!tradeConfig) return null; 

        const targetFR =
          fundingRate?.[tradeConfig?.target.value]?.[trade.base_asset]?.[0];
        const originFR =
          fundingRate?.[tradeConfig?.origin.value]?.[trade.base_asset]?.[0];

        const autoRepeat = repeatTrades?.find(
          (item) => item.trade_uuid === trade.uuid
        );

        // --- Refactor autoRepeatStatus calculation ---
        let calculatedAutoRepeatStatus = '-'; // Default value
        const autoRepeatSwitchValue = !!autoRepeat?.auto_repeat_switch; // Convert to boolean for clarity

        if (trade.trade_capital !== null) { // Only for Auto Trades
          if (autoRepeat?.status) {
            calculatedAutoRepeatStatus = autoRepeat.status; // Use status if available
          } else {
             // If no specific status, determine based on the switch
             calculatedAutoRepeatStatus = autoRepeatSwitchValue ? t('Normal') : t('Operable');
          }
        }
        // --- End Refactor ---

        const targetIconUrl = typeof tradeConfig.target?.icon === 'string' ? tradeConfig.target.icon : null;
        const originIconUrl = typeof tradeConfig.origin?.icon === 'string' ? tradeConfig.origin.icon : null;

        return {
          ...trade,
          baseAsset: trade.base_asset,
          name: trade.base_asset,
          entry: trade.low,
          exit: trade.high,
          tradeCapital: trade.trade_capital,
          created: trade.registered_datetime,
          isTether: trade.usdt_conversion,
          isDeleteLoading,
          status: trade.trade_switch,
          ...(targetFR
            ? {
                targetFundingRate: targetFR.funding_rate * 100,
                targetFundingRateIcon:
                  marketCodeCombination?.value === 'ALL'
                    ? tradeConfig.target?.icon // Pass element or URL based on what it is
                    : null,
                targetFR,
              }
            : { targetFundingRate: !fundingRate ? undefined : null }),
          ...(originFR
            ? {
                originFundingRate: originFR.funding_rate * 100,
                originFundingRateIcon:
                  marketCodeCombination?.value === 'ALL'
                    ? tradeConfig.origin?.icon // Pass element or URL based on what it is
                    : null,
                originFR,
              }
            : { originFundingRate: !fundingRate ? undefined : null }),
          marketCodes: {
            targetMarketCode: tradeConfig.target?.value,
            originMarketCode: tradeConfig.origin?.value, 
          },
          targetMarketIcon: targetIconUrl, 
          originMarketIcon: originIconUrl,
          icon: assetsData?.[trade.base_asset]?.icon,
          autoRepeatSwitch: trade.trade_capital !== null ? autoRepeatSwitchValue : null, 
          autoRepeatStatus: calculatedAutoRepeatStatus, 
          autoRepeat,
        };
      })
      // Filter out any null results from the map if tradeConfig was somehow missing
      .filter(Boolean);
  }, [
    data,
    fundingRate,
    repeatTrades,
    assetsData,
    selectedAsset,
    marketCodeCombination,
    selectedTriggerType,
    tradeConfigAllocations,
    isDeleteLoading,
    isExitTradeLoading,
    i18n.language,
    triggerScannerUuid,
  ]);

  const capitalTotals = useMemo(() => {
    if (
      !tableData ||
      !marketCodeCombination ||
      marketCodeCombination?.value === 'ALL' ||
      !marketCodeCombination?.tradeConfigUuid
    ) {
      return null;
    }

    let totalWaitingExitEntry = 0;
    let totalWaitingExit = 0;
    let totalWaitingEntry = 0;

    tableData.forEach((trade) => {
      if (
        trade.trade_capital !== null &&
        trade.trade_config_uuid === marketCodeCombination?.tradeConfigUuid
      ) {
        if (trade.status === -1) {
          totalWaitingExit += trade.trade_capital;
          totalWaitingExitEntry += trade.trade_capital;
        } else if (trade.status === 0) {
          totalWaitingEntry += trade.trade_capital;
          totalWaitingExitEntry += trade.trade_capital;
        }
      }
    });

    return {
      exitEntry: formatIntlNumber(totalWaitingExitEntry, 0),
      exit: formatIntlNumber(totalWaitingExit, 0),
      entry: formatIntlNumber(totalWaitingEntry, 0),
    };
  }, [tableData, marketCodeCombination]);

  const assetSearchProps = useMemo(
    () => ({
      apiOptions: { skip: !marketCodes },
      apiParams: { ...marketCodes, queryKey, interval: '1T' },
    }),
    [marketCodes, queryKey]
  );

  useEffect(() => {
    if (
      marketCodeCombination &&
      marketCodeCombination.value !== 'ALL' &&
      !marketCodeCombination.tradeConfigUuid &&
      !triggerScannerUuid
    )
      assetSearchRef?.current?.open();
  }, [marketCodeCombination, triggerScannerUuid]);

  useEffect(() => {
    if (selectedAsset)
      tableRef.current.getRow(`add-${selectedAsset}`)?.toggleExpanded(true);
  }, [tableData, selectedAsset]);

  const onTriggerConfigChange = useCallback(
    (value) => setTriggerConfig(value),
    []
  );

  const onAutoRepeatClick = useCallback(async (value, row) => {
    if (value) setAutoRepeatTrade(row);
    else {
      setAutoRepeatTrade();
      deleteRepeatTrade({
        id: row.autoRepeat.uuid,
        trade_config_uuid: row.trade_config_uuid,
      });
    }
  }, []);

  const getRowId = useCallback((row) => row.uuid, []);
  const onExpandedChange = useCallback((newExpanded) => {
    // Calculate the new state object, handling potential updater functions
    const newExpandedObj = isFunction(newExpanded)
      ? newExpanded()
      : newExpanded;
      
    // Get the ID of the row that WAS expanded (safe access to current state)
    const currentExpandedId = Object.keys(expanded || {})?.[0]; 
    
    // Ensure the new state object is safe before getting keys
    const safeNewExpandedObj = newExpandedObj || {};
    const newExpandedId = Object.keys(safeNewExpandedObj)?.[0];

    // If the 'add' row was expanded but now no row is expanded, clear selectedAsset
    if (currentExpandedId?.startsWith('add-') && !newExpandedId) {
         setSelectedAsset(''); 
    }
    
    // Ensure we always set an object to the state
    setExpanded(safeNewExpandedObj); 

    // Update selectedTrade based on the new expanded state
    setSelectedTrade(
      newExpandedId && !newExpandedId.startsWith('add-')
        ? tableRef.current.getRow(newExpandedId)?.original
        : undefined
    );
    setDisplayTradeHistory(false);
  }, [expanded]); // Dependency array remains correct

  const renderSubComponent = useCallback(
    ({ row: { original, toggleExpanded }, meta }) => (
      <Box sx={{ bgcolor: 'background.default', pt: 1 }}>
        <Box sx={{ m: 3 }}>
          <Button
            color="info"
            disabled={
              !meta.tradeHistoryData || meta.tradeHistoryData.length === 0
            }
            size="small"
            endIcon={
              meta.displayTradeHistory ? (
                <VisibilityOffIcon size="small" />
              ) : (
                <VisibilityIcon size="small" />
              )
            }
            onClick={() => setDisplayTradeHistory((state) => !state)}
          >
            {meta.displayTradeHistory
              ? t('Hide Trade History')
              : t('Show Trade History')}
          </Button>
        </Box>
        {meta.displayTradeHistory && (
          <Box sx={{ px: 2 }}>
            <Typography
              variant="h6"
              sx={{ fontWeight: 700, textAlign: 'center' }}
            >
              {t('Trade History')}
            </Typography>
            <TradeHistoryTable
              withPnlHistory
              marketCodes={original.marketCodes}
              tradeConfigUuid={original.trade_config_uuid}
              tradeUuid={original.uuid}
            />
          </Box>
        )}
        <Divider />
        <Box sx={{ p: { xs: 0.5, md: 2 } }}>
          <PremiumDataChartViewer
            {...meta}
            ref={premiumDataViewerRef}
            baseAssetData={{ name: original.baseAsset }}
            marketCodes={original.marketCodes}
            onIntervalChange={(newInterval) => setKlineInterval(newInterval)}
            isKimpExchange={
              isKoreanMarket(original.marketCodes.targetMarketCode) &&
              !isKoreanMarket(original.marketCodes.originMarketCode)
            }
          />
        </Box>
        {original.add ? (
          <Box sx={{ p: 2 }}>
            <AssetTradeConfig
              premiumDataViewerRef={premiumDataViewerRef}
              baseAsset={original.baseAsset}
              marketCodes={original.marketCodes}
              onTriggerConfigChange={onTriggerConfigChange}
              onCreateSuccess={() => setSelectedAsset('')}
              interval={meta.klineInterval}
              {...meta}
            />
          </Box>
        ) : (
          <UpdateTriggerForm
            baseAsset={original.baseAsset}
            defaultEntry={original.entry}
            defaultExit={original.exit}
            defaultTradeCapital={original.trade_capital}
            isTether={original.isTether}
            tradeConfigUuid={original.trade_config_uuid}
            usdtConversion={original.usdt_conversion}
            uuid={original.uuid}
            onTriggerConfigChange={onTriggerConfigChange}
            toggleExpanded={toggleExpanded}
            tradeType={original.trade_capital !== null ? 'autoTrade' : 'alarm'}
          />
        )}
      </Box>
    ),
    []
  );

  return (
    <Box sx={{ mx: { xs: 0, md: 1 }, p: { xs: 0, md: 1 } }}>
      <Stack
        direction="row"
        alignItems="flex-start"
        spacing={1}
        sx={{ mb: 2, flexWrap: 'wrap' }}
      >
        {!triggerScannerUuid && (
          <DropdownMenu
            value={selectedTriggerType}
            options={triggerTypeList}
            onSelectItem={setSelectedTriggerType}
            buttonStyle={{
              justifyContent: 'flex-start',
              minWidth: isMobile ? 100 : 220,
            }}
          />
        )}
        {/* --- START: Display Capital Totals --- */}
        {/* Only display if totals are calculated AND the selected type is NOT ALARM */}
        {capitalTotals && selectedTriggerType?.value !== 'alarms' && (
          <Box sx={{ 
            ml: 1, 
            mr: 1, 
            mt: { xs: 1, md: 0 }, 
            flexShrink: 0, 
            border: 1,
            borderColor: 'divider',
            borderRadius: 1,
            p: { xs: 0.5, md: 1 },
            bgcolor: 'background.paper'
          }}>
            <Typography 
              variant="caption" 
              sx={{ 
                display: 'block', 
                fontSize: { xs: '0.53rem', md: '0.7rem' },
                fontWeight: 500, 
                textAlign: 'right',
                mb: 0.2
              }}
            >
              {t('Total Waiting Entry/Exit')}: {capitalTotals.exitEntry} {t('KRW')}
            </Typography>
            <Typography 
              variant="caption" 
              sx={{ 
                display: 'block', 
                fontSize: { xs: '0.5rem', md: '0.7rem' },
                fontWeight: 500, 
                textAlign: 'right',
                mb: 0.2
              }}
            >
              {t('Total Waiting Exit')}: {capitalTotals.exit} {t('KRW')}
            </Typography>
            <Typography 
              variant="caption" 
              sx={{ 
                display: 'block', 
                fontSize: { xs: '0.5rem', md: '0.7rem' },
                fontWeight: 500, 
                textAlign: 'right' 
              }}
            >
              {t('Total Waiting Entry')}: {capitalTotals.entry} {t('KRW')}
            </Typography>
          </Box>
        )}
        {/* --- END: Display Capital Totals --- */}
        <Box sx={{ flexGrow: 1, minWidth: { xs: 0, sm: '10px'} }} />
        {!triggerScannerUuid && (
          <Box
            className={
              marketCodeCombination &&
              marketCodeCombination.value !== 'ALL' &&
              !marketCodeCombination.tradeConfigUuid
                ? 'animate__animated animate__pulse animate__repeat-2'
                : undefined
            }
            sx={{ ml: 'auto', mt: { xs: 1, md: 0 } }}
          >
            <AssetSearchInput
              showSelect
              ref={assetSearchRef}
              onChange={(value) => setGlobalFilter(value)}
              onSelect={(value) => {
                setGlobalFilter(value);
                setSelectedAsset(value);
              }}
              selectIcon={<AddIcon />}
              {...assetSearchProps}
            />
          </Box>
        )}
      </Stack>
      {Object.keys(rowSelection).length > 0 && !triggerScannerUuid && (
        <Stack alignItems="center" direction="row" spacing={2} sx={{ mb: 2 }}>
          <Typography sx={{ fontWeight: 700 }}>
            {t('{{selected}} of {{total}} selected', {
              selected: Object.keys(rowSelection).length,
              total: data?.length,
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
          {Object.keys(rowSelection).some(rowId => {
            const row = tableData.find(item => item.uuid === rowId);
            return row?.status === -1;
          }) && (
            <IconButton
              aria-label="Exit selected"
              color={exitTradeAlert || isExitTradeLoading ? 'error' : 'secondary'}
              onClick={() => setExitTradeAlert(true)}
              sx={{ p: 0, ':hover': { color: 'error.main' } }}
            >
              <ExitToAppIcon />
            </IconButton>
          )}
        </Stack>
      )}
      <ReactTableUI
        enableTablePaginationUI
        ref={tableRef}
        columns={columns}
        data={tableData}
        isLoading={isLoading}
        options={{
          getRowId,
          enableRowSelection: !triggerScannerUuid,
          state: { expanded, globalFilter, pagination, rowSelection },
          onExpandedChange,
          onPaginationChange: setPagination,
          onRowSelectionChange: setRowSelection,
          meta: {
            theme,
            isMobile,
            klineInterval,
            triggerConfig,
            betweenFutures,
            marketCodes: {
              targetMarketCode: marketCodeCombination?.target?.value,
              originMarketCode: marketCodeCombination?.origin?.value,
            },
            displayTradeHistory,
            tradeConfigAllocation,
            tradeHistoryData,
            onAutoRepeatClick,
            expandIcon: EditIcon,
          },
        }}
        renderSubComponent={renderSubComponent}
        getHeaderProps={() => ({
          sx: {
            bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.100',
            fontSize: isMobile ? '0.6em' : '0.7em',
          },
        })}
        getCellProps={() => ({ sx: { height: 30 } })}
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
            fontSize: isMobile ? '0.8em' : '1.15em',
          },
        })}
      />
      {!triggerScannerUuid && (
        <>
          <DeleteAlert
            loading={isDeleteLoading}
            open={deleteAlert}
            title={t(
              'Are you sure you want to permanently delete the selected trigger(s)?'
            )}
            onCancel={() => setDeleteAlert(false)}
            onClose={() => setDeleteAlert(isDeleteLoading)}
            onDelete={() =>
              deleteMultipleTrades(
                Object.keys(rowSelection).map((row) => {
                  const details = tableData.find((o) => o.uuid === row);
                  return {
                    uuid: row,
                    params: { tradeConfigUuid: details.trade_config_uuid },
                  };
                })
              )
            }
          />
          <ExitTradeAlert
            loading={isExitTradeLoading}
            open={exitTradeAlert}
            title={t(
              'Are you sure you want to exit the selected trade?'
            )}
            onCancel={() => setExitTradeAlert(false)}
            onClose={() => setExitTradeAlert(isExitTradeLoading)}
            onExitTrade={() =>
              exitMultipleTrades(
                Object.keys(rowSelection).map((row) => {
                  const details = tableData.find((o) => o.uuid === row);
                  return {
                    uuid: row,
                    params: { 
                      trade_config_uuid: details.trade_config_uuid,
                      trade_uuid: details.uuid
                     },
                  };
                })
              )
            }
          />
          <Dialog
            fullWidth
            maxWidth="sm"
            open={!!autoRepeatTrade}
            onClose={() => setAutoRepeatTrade()}
          >
            <DialogTitle>{t('Auto Repeat Configuration')}</DialogTitle>
            <DialogContent>
              <AutoRepeatForm
                {...autoRepeatTrade}
                tradeConfigUuid={autoRepeatTrade?.trade_config_uuid}
                tradeUuid={autoRepeatTrade?.uuid}
                onSuccess={() => setAutoRepeatTrade()}
              />
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setAutoRepeatTrade()}>{t('Cancel')}</Button>
              <Button form="auto-repeat-form" type="submit">
                {t('Turn on repeat transactions')}
              </Button>
            </DialogActions>
          </Dialog>
        </>
      )}
    </Box>
  );
}
