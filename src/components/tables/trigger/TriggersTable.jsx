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

import CheckBoxIcon from '@mui/icons-material/CheckBox';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';

import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import { Trans, useTranslation } from 'react-i18next';
import { DateTime } from 'luxon';

import {
  useDeleteMultipleTradesMutation,
  useGetAllTradesQuery,
} from 'redux/api/drf/tradecore';

import { useSelector } from 'react-redux';

import orderBy from 'lodash/orderBy';
import uniqBy from 'lodash/uniqBy';

import isKoreanMarket from 'utils/isKoreanMarket';

import DropdownMenu from 'components/DropdownMenu';
import MarketCodeCombinationFilter from 'components/MarketCodeCombinationFilter';
import PremiumDataChartViewer from 'components/PremiumDataChartViewer';
import ReactTableUI from 'components/ReactTableUI';
import UpdateAlarmForm from 'components/UpdateAlarmForm';

import { MARKET_CODE_LIST, TRIGGER_LIST } from 'constants/lists';

import renderExpandCell from 'components/tables/common/renderExpandCell';
import renderSelectCell from './renderSelectCell';
import renderValueCell from './renderValueCell';
import renderSelectHeader from './renderSelectHeader';

export default function TriggersTable() {
  const tableRef = useRef();
  const { i18n, t } = useTranslation();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const { user } = useSelector((state) => state.auth);

  const tradeConfigAllocations = useMemo(
    () =>
      user?.trade_config_allocations?.map((tradeConfig) => {
        const target = MARKET_CODE_LIST.find(
          (o) => o.value === tradeConfig.target_market_code
        );
        const origin = MARKET_CODE_LIST.find(
          (o) => o.value === tradeConfig.origin_market_code
        );
        return {
          target,
          origin,
          uuid: tradeConfig.trade_config_uuid,
          value: `${tradeConfig.target_market_code}:${tradeConfig.origin_market_code}`,
        };
      }) || [],
    [user?.trade_config_allocations]
  );

  const tradeConfigUuids = useMemo(
    () => user?.trade_config_allocations?.map((o) => o.trade_config_uuid) || [],
    [user?.trade_config_allocations]
  );

  const [expanded, setExpanded] = useState({});
  const [pagination, setPagination] = useState({
    pageIndex: 0,
    pageSize: 100,
  });
  const [rowSelection, setRowSelection] = useState({});

  const [deleteAlert, setDeleteAlert] = useState(false);

  const [alarmConfig, setAlarmConfig] = useState();
  const [marketCodeCombinationList, setMarketCodeCombinationList] = useState(
    []
  );
  const [selectedMarketCodeCombination, setSelectedMarketCodeCombination] =
    useState();

  const [triggerList, setTriggerList] = useState([]);
  const [selectedTrigger, setSelectedTrigger] = useState();

  const { data, isFetching, isLoading } = useGetAllTradesQuery(
    { tradeConfigUuids }
    // { skip: !tradeConfigAllocation }
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
    const marketCodes = [
      {
        label: t('All Market Code Combinations'),
        value: 'ALL',
        icon: <CheckBoxIcon />,
      },
    ].concat(
      data?.map((item) => {
        const tradeConfig = tradeConfigAllocations.find(
          (o) => o.uuid === item.trade_config_uuid
        );
        return {
          value: tradeConfig?.value,
          target: {
            label: tradeConfig?.target.getLabel(),
            icon: (
              <Box
                component="img"
                src={tradeConfig?.target.icon}
                alt={tradeConfig?.target.getLabel()}
                sx={{
                  height: { xs: 16, md: 18 },
                  width: { xs: 16, md: 18 },
                }}
              />
            ),
          },
          origin: {
            label: tradeConfig?.origin.getLabel(),
            icon: (
              <Box
                component="img"
                src={tradeConfig?.origin.icon}
                alt={tradeConfig?.origin.getLabel()}
                sx={{
                  height: { xs: 16, md: 18 },
                  width: { xs: 16, md: 18 },
                }}
              />
            ),
          },
          tradeConfigUuid: tradeConfig.uuid,
        };
      })
    );
    setMarketCodeCombinationList(uniqBy(marketCodes, 'value'));
    if (!selectedMarketCodeCombination)
      setSelectedMarketCodeCombination(marketCodes[0]);
  }, [
    data,
    selectedMarketCodeCombination,
    tradeConfigAllocations,
    i18n.language,
  ]);

  useEffect(() => {
    const triggers = TRIGGER_LIST.map((trigger) => ({
      label: trigger.getLabel(),
      value: trigger.value,
      icon: <trigger.icon />,
      disabled: trigger.value === 'autoTrade',
    }));
    setTriggerList(triggers);
    if (!selectedTrigger) setSelectedTrigger(triggers[0]);
  }, [selectedTrigger, i18n.language]);

  const columns = useMemo(
    () => [
      {
        accessorKey: 'select',
        enableSorting: false,
        size: isMobile ? 20 : 50,
        header: renderSelectHeader,
        cell: renderSelectCell,
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
      },
      {
        accessorKey: 'registered',
        header: t('Registration Date'),
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

  const tableData = useMemo(
    () =>
      orderBy(
        data?.filter((item) => {
          let flag = selectedMarketCodeCombination?.value === 'ALL';
          if (selectedMarketCodeCombination?.value !== 'ALL')
            flag =
              selectedMarketCodeCombination?.tradeConfigUuid ===
              item.trade_config_uuid;
          return flag;
        }) || [],
        'registered_datetime',
        'desc'
      ).map((trade) => {
        const tradeConfig = tradeConfigAllocations.find(
          (o) => o.uuid === trade.trade_config_uuid
        );
        return {
          entry: trade.low,
          exit: trade.high,
          registered: DateTime.fromISO(
            trade.registered_datetime
          ).toLocaleString(DateTime.DATETIME_MED),
          isTether: trade.usdt_conversion,
          isDeleteLoading,
          marketCodes: {
            targetMarketCode: tradeConfig.target.value,
            originMarketCode: tradeConfig.origin.value,
          },
          ...trade,
        };
      }),
    [
      data,
      selectedMarketCodeCombination,
      tradeConfigAllocations,
      isDeleteLoading,
    ]
  );

  const onAlarmConfigChange = useCallback((value) => setAlarmConfig(value), []);

  const getRowId = useCallback((row) => row.uuid, []);
  const onExpandedChange = useCallback(
    (newExpanded) => setExpanded(newExpanded()),
    []
  );

  const renderSubComponent = useCallback(
    ({ row: { original, toggleExpanded }, meta }) => (
      <Box sx={{ bgcolor: 'background.default' }}>
        <PremiumDataChartViewer
          baseAssetData={{ name: original.base_asset }}
          marketCodes={original.marketCodes}
          isKimpExchange={
            isKoreanMarket(original.marketCodes.targetMarketCode) &&
            !isKoreanMarket(original.marketCodes.originMarketCode)
          }
          {...meta}
        />
        <UpdateAlarmForm
          row={original}
          onAlarmConfigChange={onAlarmConfigChange}
          toggleExpanded={toggleExpanded}
        />
      </Box>
    ),
    []
  );

  return (
    <Box sx={{ mx: { xs: 0, md: 1 }, p: { xs: 0, md: 1 } }}>
      <Stack
        useFlexGap
        direction="row"
        flexWrap="wrap"
        sx={{ mb: 2 }}
        spacing={1}
      >
        <MarketCodeCombinationFilter
          options={marketCodeCombinationList}
          value={selectedMarketCodeCombination}
          onSelectItem={setSelectedMarketCodeCombination}
        />
        <DropdownMenu
          value={selectedTrigger}
          options={triggerList}
          onSelectItem={setSelectedTrigger}
          buttonStyle={{
            justifyContent: 'flex-start',
            minWidth: isMobile ? 190 : 220,
          }}
        />
      </Stack>
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
        data={tableData}
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
            alarmConfig,
            expandIcon: EditIcon,
            // onAlarmConfigChange,
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
            fontSize: isMobile ? '0.8em' : '1em',
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
