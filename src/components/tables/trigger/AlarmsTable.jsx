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

import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';

import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import { Trans, useTranslation } from 'react-i18next';
import { DateTime } from 'luxon';

import {
  useDeleteMultipleTradesMutation,
  useGetTradesByTradeConfigQuery,
} from 'redux/api/drf/tradecore';

import isEmpty from 'lodash/isEmpty';
import orderBy from 'lodash/orderBy';

import ReactTableUI from 'components/ReactTableUI';
import UpdateAlarmForm from 'components/UpdateAlarmForm';

import renderExpandCell from 'components/tables/common/renderExpandCell';
import renderSelectCell from './renderSelectCell';
import renderValueCell from './renderValueCell';
import renderSelectHeader from './renderSelectHeader';

export default function AlarmsTable({
  baseAsset,
  tradeConfigAllocation,
  onAlarmConfigChange,
  createAlarmFormRef,
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
    { skip: !tradeConfigAllocation }
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
    if (!isEmpty(expanded)) createAlarmFormRef.current.setDisabled(true);
    else createAlarmFormRef.current.setDisabled(false);
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

  const data = useMemo(
    () =>
      orderBy(trades || [], 'registered_datetime', 'desc').map((trade) => ({
        entry: trade.low,
        exit: trade.high,
        registered: DateTime.fromISO(trade.registered_datetime).toLocaleString(
          DateTime.DATETIME_MED
        ),
        isTether: trade.usdt_conversion,
        isDeleteLoading,
        ...trade,
      })),
    [trades, isDeleteLoading]
  );

  const getRowId = useCallback((row) => row.uuid, []);
  const onExpandedChange = useCallback(
    (newExpanded) => setExpanded(newExpanded()),
    []
  );

  const renderSubComponent = useCallback(
    ({ row: { original, toggleExpanded }, meta }) => (
      <Box sx={{ bgcolor: 'background.default' }}>
        <UpdateAlarmForm
          row={original}
          onAlarmConfigChange={meta.onAlarmConfigChange}
          toggleExpanded={toggleExpanded}
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
          meta: { theme, isMobile, onAlarmConfigChange, expandIcon: EditIcon },
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
      <Dialog
        open={deleteAlert}
        onClose={() => setDeleteAlert(isDeleteLoading)}
        aria-labelledby="delete-alert-title"
        aria-describedby="delete-alert-description"
      >
        {isDeleteLoading && <LinearProgress />}
        <DialogTitle id="delete-alert-title">
          {t(
            'Are you sure you want to permanently delete the selected alarm(s)?'
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
                Object.keys(rowSelection).map((row) => ({
                  uuid: row,
                  params: {
                    tradeConfigUuid: tradeConfigAllocation?.trade_config_uuid,
                  },
                }))
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
