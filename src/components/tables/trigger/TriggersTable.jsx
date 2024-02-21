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
import InputAdornment from '@mui/material/InputAdornment';
import OutlinedInput from '@mui/material/OutlinedInput';
import IconButton from '@mui/material/IconButton';
import LinearProgress from '@mui/material/LinearProgress';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

import CloseIcon from '@mui/icons-material/Close';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import SearchIcon from '@mui/icons-material/Search';
import SyncAltIcon from '@mui/icons-material/SyncAlt';

import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import { Trans, useTranslation } from 'react-i18next';
import { DateTime } from 'luxon';

import {
  useDeleteMultipleTradesMutation,
  useGetAllTradesQuery,
} from 'redux/api/drf/tradecore';

import debounce from 'lodash/debounce';
import orderBy from 'lodash/orderBy';

import isKoreanMarket from 'utils/isKoreanMarket';

import DropdownMenu from 'components/DropdownMenu';
import PremiumDataChartViewer from 'components/PremiumDataChartViewer';
import ReactTableUI from 'components/ReactTableUI';
import UpdateAlarmForm from 'components/UpdateAlarmForm';

import { TRIGGER_LIST } from 'constants/lists';

import renderExpandCell from 'components/tables/common/renderExpandCell';
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
  const { i18n, t } = useTranslation();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [expanded, setExpanded] = useState({});
  const [globalFilter, setGlobalFilter] = useState('');
  const [pagination, setPagination] = useState({
    pageIndex: 0,
    pageSize: 100,
  });
  const [rowSelection, setRowSelection] = useState({});

  const [deleteAlert, setDeleteAlert] = useState(false);

  const [alarmConfig, setAlarmConfig] = useState();

  const [triggerTypeList, setTriggerTypeList] = useState([]);
  const [selectedTriggerType, setSelectedTriggerType] = useState();

  const [searchValue, setSearchValue] = useState('');

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

  const tableData = useMemo(
    () =>
      orderBy(
        data?.filter((item) => {
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
        }) || [],
        'registered_datetime',
        'desc'
      ).map((trade) => {
        const tradeConfig = tradeConfigAllocations.find(
          (o) => o.uuid === trade.trade_config_uuid
        );
        return {
          ...trade,
          baseAsset: trade.base_asset,
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
        };
      }),
    [
      data,
      selectedMarketCodeCombination,
      selectedTriggerType,
      tradeConfigAllocations,
      isDeleteLoading,
    ]
  );

  const onChange = (value) => setGlobalFilter(value);
  const debouncedOnChange = useCallback(
    debounce(onChange, 500, { leading: false, trailing: true })
  );

  useEffect(() => {
    debouncedOnChange(searchValue);
  }, [searchValue]);

  const onAlarmConfigChange = useCallback((value) => setAlarmConfig(value), []);

  const getRowId = useCallback((row) => row.uuid, []);
  const onExpandedChange = useCallback(
    (newExpanded) => setExpanded(newExpanded()),
    []
  );

  const renderSubComponent = useCallback(
    ({ row: { original, toggleExpanded }, meta }) => (
      <Box sx={{ bgcolor: 'background.default' }}>
        <Box sx={{ p: { xs: 0.5, md: 2 } }}>
          <PremiumDataChartViewer
            baseAssetData={{ name: original.baseAsset }}
            marketCodes={original.marketCodes}
            isKimpExchange={
              isKoreanMarket(original.marketCodes.targetMarketCode) &&
              !isKoreanMarket(original.marketCodes.originMarketCode)
            }
            {...meta}
          />
        </Box>
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
        <OutlinedInput
          size="small"
          placeholder={t('Search')}
          onChange={(e) => setSearchValue(e.target.value)}
          value={searchValue}
          startAdornment={
            <InputAdornment position="start">
              <SearchIcon sx={isMobile ? { fontSize: '1em' } : {}} />
            </InputAdornment>
          }
          endAdornment={
            <InputAdornment
              position="end"
              sx={{ cursor: 'pointer', ':hover': { opacity: 0.5 } }}
            >
              <CloseIcon
                onClick={() => {
                  setGlobalFilter('');
                  setSearchValue('');
                }}
                sx={isMobile ? { fontSize: '1em' } : {}}
              />
            </InputAdornment>
          }
          // inputProps={{
          //   style: isSmallScreen ? { height: '0.5em', width: 60 } : {},
          // }}
          sx={{
            '& .MuiInputBase-root': { px: { xs: 0.5, sm: 1 } },
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
          state: { expanded, globalFilter, pagination, rowSelection },
          onExpandedChange,
          onPaginationChange: setPagination,
          onRowSelectionChange: setRowSelection,
          meta: {
            theme,
            isMobile,
            alarmConfig,
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
