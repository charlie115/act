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
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import IconButton from '@mui/material/IconButton';
import LinearProgress from '@mui/material/LinearProgress';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import SyncAltIcon from '@mui/icons-material/SyncAlt';

import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import { Trans, useTranslation } from 'react-i18next';
import { DateTime } from 'luxon';

import { useGetAssetsQuery } from 'redux/api/drf/infocore';
import {
  useDeleteMultipleTradesMutation,
  useGetAllTradesQuery,
} from 'redux/api/drf/tradecore';

import { useSelector } from 'react-redux';

import isFunction from 'lodash/isFunction';

import isKoreanMarket from 'utils/isKoreanMarket';

import AssetSearchInput from 'components/AssetSearchInput';
import CreateAlarmForm from 'components/CreateAlarmForm';
import DropdownMenu from 'components/DropdownMenu';
import PremiumDataChartViewer from 'components/PremiumDataChartViewer';
import ReactTableUI from 'components/ReactTableUI';
import UpdateAlarmForm from 'components/UpdateAlarmForm';

import { TRIGGER_LIST } from 'constants/lists';

import renderExpandCell from 'components/tables/common/renderExpandCell';
import renderIconCell from 'components/tables/common/renderIconCell';
import renderMarketCodesCell from './renderMarketCodesCell';
import renderSelectCell from './renderSelectCell';
import renderStatusCell from './renderStatusCell';
import renderValueCell from './renderValueCell';

import renderSelectHeader from './renderSelectHeader';

export default function TriggersTable({
  selectedMarketCodeCombination,
  tradeConfigAllocations,
  tradeConfigUuids,
}) {
  const tableRef = useRef();
  const assetSearchRef = useRef();
  const { i18n, t } = useTranslation();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const { user } = useSelector((state) => state.auth);

  const [expanded, setExpanded] = useState({});
  const [globalFilter, setGlobalFilter] = useState('');
  const [pagination, setPagination] = useState({
    pageIndex: 0,
    pageSize: 100,
  });
  const [rowSelection, setRowSelection] = useState({});

  const [selectedAsset, setSelectedAsset] = useState('');

  const [deleteAlert, setDeleteAlert] = useState(false);

  const [alarmConfig, setAlarmConfig] = useState();

  const [triggerTypeList, setTriggerTypeList] = useState([]);
  const [selectedTriggerType, setSelectedTriggerType] = useState();

  const { data, isFetching, isLoading } = useGetAllTradesQuery(
    { tradeConfigUuids },
    { pollingInterval: 1000 * 60 }
  );

  const [
    deleteMultipleTrades,
    { isLoading: isDeleteLoading, isSuccess: isDeleteSuccess },
  ] = useDeleteMultipleTradesMutation();

  const { data: assetsData } = useGetAssetsQuery();

  const marketCodes = useMemo(() => {
    if (
      !selectedMarketCodeCombination?.value ||
      selectedMarketCodeCombination.value === 'ALL'
    )
      return null;
    return {
      targetMarketCode: selectedMarketCodeCombination?.target.value,
      originMarketCode: selectedMarketCodeCombination?.origin.value,
    };
  }, [selectedMarketCodeCombination?.value]);

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
      disabled: trigger.value === 'autoTrade',
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
        size: isMobile ? 20 : 50,
        header: renderSelectHeader,
        cell: renderSelectCell,
      },
      {
        accessorKey: 'icon',
        enableGlobalFilter: false,
        enableSorting: false,
        maxSize: 10,
        header: <span />,
        cell: renderIconCell,
      },
      {
        accessorKey: 'baseAsset',
        size: 80,
        header: t('Base Asset'),
      },
      {
        accessorKey: 'marketCodes',
        enableGlobalFilter: false,
        enableSorting: false,
        size: isMobile ? 80 : 140,
        header: <SyncAltIcon />,
        cell: renderMarketCodesCell,
      },
      {
        accessorKey: 'entry',
        size: isMobile ? 80 : 140,
        header: t('Entry'),
        cell: renderValueCell,
      },
      {
        accessorKey: 'exit',
        size: isMobile ? 80 : 140,
        header: t('Exit'),
        cell: renderValueCell,
      },
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
    [i18n.language, isMobile]
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
            targetMarketCode: selectedMarketCodeCombination?.target.value,
            originMarketCode: selectedMarketCodeCombination?.origin.value,
          },
          status: null,
          add: true,
        },
      ];

    return data
      ?.filter((item) => {
        if (!item) return false;

        let flag = selectedMarketCodeCombination?.value === 'ALL';
        if (selectedMarketCodeCombination?.value !== 'ALL')
          flag =
            selectedMarketCodeCombination?.tradeConfigUuid ===
            item.trade_config_uuid;
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
        return {
          ...trade,
          baseAsset: trade.base_asset,
          name: trade.base_asset,
          entry: trade.low,
          exit: trade.high,
          created: DateTime.fromISO(trade.registered_datetime).toLocaleString(
            DateTime.DATETIME_MED
          ),
          isTether: trade.usdt_conversion,
          isDeleteLoading,
          status: trade.trigger_switch,
          marketCodes: {
            targetMarketCode: tradeConfig.target.value,
            originMarketCode: tradeConfig.origin.value,
          },
          icon: assetsData?.[trade.base_asset]?.icon,
        };
      });
  }, [
    data,
    assetsData,
    selectedAsset,
    selectedMarketCodeCombination,
    selectedTriggerType,
    tradeConfigAllocations,
    isDeleteLoading,
  ]);

  const assetSearchProps = useMemo(
    () => ({
      apiOptions: { skip: !marketCodes },
      apiParams: { ...marketCodes, interval: '1T' },
    }),
    [marketCodes]
  );

  useEffect(() => {
    if (
      selectedMarketCodeCombination &&
      selectedMarketCodeCombination.value !== 'ALL' &&
      !selectedMarketCodeCombination.tradeConfigUuid
    )
      assetSearchRef?.current?.open();
  }, [selectedMarketCodeCombination]);

  useEffect(() => {
    if (selectedAsset)
      tableRef.current.getRow(`add-${selectedAsset}`)?.toggleExpanded(true);
  }, [tableData, selectedAsset]);

  const onAlarmConfigChange = useCallback((value) => setAlarmConfig(value), []);

  const getRowId = useCallback((row) => row.uuid, []);
  const onExpandedChange = useCallback((newExpanded) => {
    setExpanded(isFunction(newExpanded) ? newExpanded() : newExpanded);
  }, []);

  const renderSubComponent = useCallback(
    ({ row: { original, toggleExpanded }, meta }) => (
      <Box sx={{ bgcolor: 'background.default' }}>
        <Box sx={{ p: { xs: 0.5, md: 2 } }}>
          <PremiumDataChartViewer
            {...meta}
            baseAssetData={{ name: original.baseAsset }}
            marketCodes={original.marketCodes}
            isKimpExchange={
              isKoreanMarket(original.marketCodes.targetMarketCode) &&
              !isKoreanMarket(original.marketCodes.originMarketCode)
            }
          />
        </Box>
        {original.add ? (
          <Box sx={{ p: 2 }}>
            <CreateAlarmForm
              baseAsset={original.baseAsset}
              marketCodes={original.marketCodes}
              tradeConfigAllocation={meta.tradeConfigAllocation}
              onAlarmConfigChange={onAlarmConfigChange}
              onCreateSuccess={() => setSelectedAsset('')}
            />
          </Box>
        ) : (
          <UpdateAlarmForm
            baseAsset={original.baseAsset}
            defaultEntry={original.entry}
            defaultExit={original.exit}
            isTether={original.isTether}
            tradeConfigUuid={original.trade_config_uuid}
            usdtConversion={original.usdt_conversion}
            uuid={original.uuid}
            onAlarmConfigChange={onAlarmConfigChange}
            toggleExpanded={toggleExpanded}
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
            selectedMarketCodeCombination &&
            selectedMarketCodeCombination.value !== 'ALL' &&
            !selectedMarketCodeCombination.tradeConfigUuid
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
            alarmConfig,
            tradeConfigAllocation,
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
            fontSize: isMobile ? '0.8em' : '1.15em',
            width: isMobile ? 'auto' : undefined,
          },
        })}
      />
      <Dialog
        open={deleteAlert}
        onClose={() => setDeleteAlert(isDeleteLoading)}
        aria-labelledby="delete-alert-title"
        aria-describedby="delete-alert-description"
      >
        {isDeleteLoading && <LinearProgress />}
        <DialogTitle id="delete-alert-title">
          {t(
            'Are you sure you want to permanently delete the selected trigger(s)?'
          )}
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="delete-alert-description">
            <Trans>
              This action is{' '}
              <strong style={{ textTransform: 'underline' }}>
                irreversible
              </strong>
              !
            </Trans>{' '}
            {t('Do you wish to continue?')}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button
            autoFocus
            color="secondary"
            disabled={isDeleteLoading}
            onClick={() => setDeleteAlert(false)}
          >
            {t('Cancel')}
          </Button>
          <Button
            color="error"
            variant="contained"
            disabled={isDeleteLoading}
            onClick={() =>
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
          >
            {t('Delete')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
