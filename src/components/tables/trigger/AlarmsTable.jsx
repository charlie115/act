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

import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import DeleteIcon from '@mui/icons-material/Delete';

import { Trans, useTranslation } from 'react-i18next';
import { DateTime } from 'luxon';

import {
  useDeleteMultipleTradesMutation,
  useGetTradesQuery,
} from 'redux/api/drf/tradecore';

import orderBy from 'lodash/orderBy';

import ReactTableUI from 'components/ReactTableUI';

import renderSelectCell from './renderSelectCell';
import renderValueCell from './renderValueCell';

import renderSelectHeader from './renderSelectHeader';

export default function AlarmsTable({ baseAsset, tradeConfigAllocation }) {
  const tableRef = useRef();
  const { i18n, t } = useTranslation();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 10 });
  const [rowSelection, setRowSelection] = useState({});

  const [deleteAlert, setDeleteAlert] = useState(false);

  const {
    data: trades,
    isFetching,
    isLoading,
  } = useGetTradesQuery(
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

  const columns = useMemo(
    () => [
      {
        accessorKey: 'select',
        enableSorting: false,
        size: 50,
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

  return (
    <Box sx={{ mx: 4, p: 2 }}>
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
          state: { pagination, rowSelection },
          onPaginationChange: setPagination,
          onRowSelectionChange: setRowSelection,
        }}
        getHeaderProps={() => ({
          sx: {
            bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.100',
            px: 2,
          },
        })}
        getCellProps={() => ({ sx: { height: 30, px: 2 } })}
        getTableProps={() => ({
          sx: {
            border: 1,
            borderColor: 'divider',
            fontSize: '1.2em',
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
            'Are you sure you want to permanently delete the selected alarms?'
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
            // variant="filled"
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
              deleteMultipleTrades({
                ids: Object.keys(rowSelection),
                params: {
                  tradeConfigUuid: tradeConfigAllocation?.trade_config_uuid,
                },
              })
            }
          >
            {t('Delete')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
