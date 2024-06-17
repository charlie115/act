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
import SyncAltIcon from '@mui/icons-material/SyncAlt';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';

import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import { useTranslation } from 'react-i18next';
import { DateTime } from 'luxon';

import {
  useGetAssetsQuery,
  useGetFundingRateByMarketCodeQuery,
} from 'redux/api/drf/infocore';
import {
  useDeleteMultipleTradesMutation,
  useDeleteRepeatTradeMutation,
  useGetAllRepeatTradesQuery,
  useGetAllTradesQuery,
  useGetTradeHistoryQuery,
} from 'redux/api/drf/tradecore';

import { useSelector } from 'react-redux';

import isFunction from 'lodash/isFunction';

import isKoreanMarket from 'utils/isKoreanMarket';

import AssetSearchInput from 'components/AssetSearchInput';
import AssetTradeConfig from 'components/AssetTradeConfig';
import AutoRepeatForm from 'components/AutoRepeatForm';
import DeleteAlert from 'components/DeleteAlert';
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

  const [triggerConfig, setTriggerConfig] = useState();

  const [triggerTypeList, setTriggerTypeList] = useState([]);
  const [selectedTriggerType, setSelectedTriggerType] = useState();

  const [selectedTrade, setSelectedTrade] = useState();
  const [displayTradeHistory, setDisplayTradeHistory] = useState(false);

  const [klineInterval, setKlineInterval] = useState('1T');

  const { data, isFetching, isLoading, isSuccess } = useGetAllTradesQuery(
    { tradeConfigUuids },
    { pollingInterval: 1000 * 60, skip: !!autoRepeatTrade }
  );

  const { data: repeatTrades } = useGetAllRepeatTradesQuery({
    tradeConfigUuids,
  });

  const [deleteRepeatTrade] = useDeleteRepeatTradeMutation();

  const [
    deleteMultipleTrades,
    { isLoading: isDeleteLoading, isSuccess: isDeleteSuccess },
  ] = useDeleteMultipleTradesMutation();

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
    if (!marketCodeCombination?.value || marketCodeCombination.value === 'ALL')
      return null;
    return {
      targetMarketCode: marketCodeCombination?.target.value,
      originMarketCode: marketCodeCombination?.origin.value,
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
    const triggers = TRIGGER_LIST.map((trigger) => ({
      label: trigger.getLabel(),
      value: trigger.value,
      icon: <trigger.icon />,
      // disabled: trigger.value === 'autoTrade',
    }));
    setTriggerTypeList(triggers);
    if (!selectedTriggerType) setSelectedTriggerType(triggers[0]);
  }, [selectedTriggerType, i18n.language]);

  const columns = useMemo(
    () => [
      {
        accessorKey: 'select',
        enableGlobalFilter: false,
        enableSorting: false,
        size: isMobile ? 15 : 30,
        header: renderSelectHeader,
        cell: renderSelectCell,
      },
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
        size: isMobile ? 30 : 50,
        header: t('Base Asset'),
      },
      {
        accessorKey: 'marketCodes',
        enableGlobalFilter: false,
        enableSorting: false,
        size: isMobile ? 45 : 150,
        header: <SyncAltIcon />,
        cell: renderMarketCodesCell,
      },
      {
        accessorKey: 'entry',
        size: isMobile ? 25 : 80,
        header: t('Entry'),
        cell: renderValueCell,
      },
      {
        accessorKey: 'exit',
        size: isMobile ? 25 : 80,
        header: t('Exit'),
        cell: renderValueCell,
      },
      {
        accessorKey: 'tradeCapital',
        size: isMobile ? 25 : 80,
        header: t('Trade Capital'),
        cell: renderCurrencyFormatCell,
      },
      {
        accessorKey: 'status',
        size: isMobile ? 30 : 65,
        header: t('Status'),
        cell: renderStatusCell,
      },
      ...(marketCodeCombination.value === 'ALL' && !isMobile
        ? [
            {
              accessorKey: 'targetFundingRate',
              header: t('Funding Rate'),
              size: isMobile ? 25 : 80,
              cell: renderFundingRateCell,
            },
            {
              accessorKey: 'originFundingRate',
              header: t('Funding Rate'),
              size: isMobile ? 25 : 80,
              cell: renderFundingRateCell,
            },
          ]
        : []),
      ...(marketCodeCombination.target &&
      !marketCodeCombination.target.isSpot &&
      !isMobile
        ? [
            {
              accessorKey: 'targetFundingRate',
              header: renderFundingRateHeader,
              cell: renderFundingRateCell,
              size: isMobile ? 25 : 80,
            },
          ]
        : []),
      ...(marketCodeCombination.origin &&
      !marketCodeCombination.origin.isSpot &&
      !isMobile
        ? [
            {
              accessorKey: 'originFundingRate',
              header: renderFundingRateHeader,
              cell: renderFundingRateCell,
              size: isMobile ? 25 : 80,
            },
          ]
        : []),
      {
        accessorKey: 'autoRepeatStatus',
        size: isMobile ? 30 : 75,
        header: t('Repeat Transaction Status'),
        slotProps: { cell: { sx: { fontSize: 12 } } },
      },
      {
        accessorKey: 'autoRepeatSwitch',
        size: isMobile ? 35 : 80,
        header: t('Auto Repeat'),
        cell: renderAutoRepeatSwitchCell,
        props: { sx: { textAlign: 'center' } },
      },
      {
        accessorKey: 'created',
        size: isMobile ? 40 : 110,
        header: t('Created'),
        props: { sx: { fontSize: 11 } },
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
    [marketCodeCombination, i18n.language, isMobile]
  );

  const tableData = useMemo(() => {
    if (!data) return [];
    if (selectedAsset)
      return [
        {
          uuid: `add-${selectedAsset}`,
          baseAsset: selectedAsset,
          name: selectedAsset,
          icon: assetsData?.[selectedAsset]?.icon,
          marketCodes: {
            targetMarketCode: marketCodeCombination?.target.value,
            originMarketCode: marketCodeCombination?.origin.value,
          },
          status: null,
          add: true,
        },
      ];

    return data
      ?.filter((item) => {
        if (!item) return false;

        let flag = marketCodeCombination?.value === 'ALL';
        if (marketCodeCombination?.value !== 'ALL')
          flag =
            marketCodeCombination?.tradeConfigUuid === item.trade_config_uuid;
        if (selectedTriggerType?.value !== 'ALL')
          flag =
            flag && selectedTriggerType?.value === 'alarms'
              ? item.trade_capital === null
              : item.trade_capital !== null;
        return flag;
      })
      .map((trade) => {
        const tradeConfig = tradeConfigAllocations.find(
          (o) => o.uuid === trade.trade_config_uuid
        );

        const targetFR =
          fundingRate?.[tradeConfig?.target.value]?.[trade.base_asset]?.[0];
        const originFR =
          fundingRate?.[tradeConfig?.origin.value]?.[trade.base_asset]?.[0];

        const autoRepeat = repeatTrades?.find(
          (item) => item.trade_uuid === trade.uuid
        );
        let autoRepeatStatus = '-';
        let autoRepeatSwitch = null;
        if (trade.trade_capital !== null) {
          if (autoRepeat?.status) autoRepeatStatus = autoRepeat.status;
          else
            autoRepeatStatus = autoRepeat?.auto_repeat_switch
              ? t('Normal')
              : t('Operable');
          autoRepeatSwitch = !!autoRepeat?.auto_repeat_switch;
        }

        return {
          ...trade,
          baseAsset: trade.base_asset,
          name: trade.base_asset,
          entry: trade.low,
          exit: trade.high,
          tradeCapital: trade.trade_capital,
          created: DateTime.fromISO(trade.registered_datetime, {
            zone: 'UTC',
          })
            .toLocal()
            .toLocaleString(DateTime.DATETIME_MED),
          isTether: trade.usdt_conversion,
          isDeleteLoading,
          status: trade.trade_switch,
          ...(targetFR
            ? {
                targetFundingRate: targetFR.funding_rate * 100,
                targetFundingRateIcon:
                  marketCodeCombination?.value === 'ALL'
                    ? tradeConfig.target.icon
                    : null,
                targetFR,
              }
            : { targetFundingRate: !fundingRate ? undefined : null }),
          ...(originFR
            ? {
                originFundingRate: originFR.funding_rate * 100,
                originFundingRateIcon:
                  marketCodeCombination?.value === 'ALL'
                    ? tradeConfig.origin.icon
                    : null,
                originFR,
              }
            : { originFundingRate: !fundingRate ? undefined : null }),
          marketCodes: {
            targetMarketCode: tradeConfig.target.value,
            originMarketCode: tradeConfig.origin.value,
          },
          icon: assetsData?.[trade.base_asset]?.icon,
          autoRepeatSwitch,
          autoRepeatStatus,
          autoRepeat,
        };
      });
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
    i18n.language,
  ]);

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
      !marketCodeCombination.tradeConfigUuid
    )
      assetSearchRef?.current?.open();
  }, [marketCodeCombination]);

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
    const newExpandedObj = isFunction(newExpanded)
      ? newExpanded()
      : newExpanded;
    setExpanded(newExpandedObj);

    const rowId = Object.keys(newExpandedObj || {})?.[0];
    setSelectedTrade(
      rowId && !rowId.startsWith('add-')
        ? tableRef.current.getRow(rowId)?.original
        : undefined
    );
    setDisplayTradeHistory(false);
  }, []);

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
        justifyContent="space-between"
        spacing={1}
        sx={{ mb: 2 }}
      >
        <DropdownMenu
          value={selectedTriggerType}
          options={triggerTypeList}
          onSelectItem={setSelectedTriggerType}
          buttonStyle={{
            justifyContent: 'flex-start',
            minWidth: isMobile ? 190 : 220,
          }}
        />
        <Box
          className={
            marketCodeCombination &&
            marketCodeCombination.value !== 'ALL' &&
            !marketCodeCombination.tradeConfigUuid
              ? 'animate__animated animate__pulse animate__repeat-2'
              : undefined
          }
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
      </Stack>
      {Object.keys(rowSelection).length > 0 && (
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
        </Stack>
      )}
      <ReactTableUI
        enableTablePaginationUI
        ref={tableRef}
        columns={columns}
        data={tableData}
        isLoading={isLoading}
        showProgressBar={isFetching}
        options={{
          getRowId,
          enableRowSelection: true,
          state: { expanded, globalFilter, pagination, rowSelection },
          onExpandedChange,
          onPaginationChange: setPagination,
          onRowSelectionChange: setRowSelection,
          meta: {
            theme,
            isMobile,
            klineInterval,
            triggerConfig,
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
    </Box>
  );
}
