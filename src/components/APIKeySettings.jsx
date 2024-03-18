import React, { useCallback, useEffect, useMemo, useState } from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import Grid from '@mui/material/Grid';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';

import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';

import {
  useDeleteExchangeApiKeyMutation,
  useGetExchangeApiKeyQuery,
  usePostExchangeApiKeyMutation,
} from 'redux/api/drf/tradecore';

import { useTranslation } from 'react-i18next';

import { Controller, useForm } from 'react-hook-form';

import { DateTime } from 'luxon';

import truncate from 'lodash/truncate';

import DeleteAlert from 'components/DeleteAlert';
import ReactTableUI from 'components/ReactTableUI';

import renderActionIconCell from 'components/tables/common/renderActionIconCell';

export default function APIKeySettings({ marketCodeCombination }) {
  const { i18n, t } = useTranslation();

  const [deleteAlert, setDeleteAlert] = useState(null);
  const [marketCodeForm, setMarketCodeForm] = useState(null);
  const [showPassphrase, setShowPassphrase] = useState(false);
  const [showSecretKey, setShowSecretKey] = useState(false);

  const handleCloseDialog = () => setMarketCodeForm(null);

  const { data: exchangeApiKeys } = useGetExchangeApiKeyQuery({
    tradeConfigUuid: marketCodeCombination.tradeConfigUuid,
  });
  const [createExchangeApiKey, createResults] = usePostExchangeApiKeyMutation();
  const [deleteExchangeApiKey, deleteResults] =
    useDeleteExchangeApiKeyMutation();

  const { control, formState, handleSubmit, reset } = useForm({
    defaultValues: { accessKey: '', secretKey: '', passphrase: '' },
    mode: 'all',
  });

  const { isValid } = formState;

  const onSubmit = (data) => {
    createExchangeApiKey({
      trade_config_uuid: marketCodeCombination.tradeConfigUuid,
      market_code: marketCodeForm.value,
      access_key: data.accessKey,
      secret_key: data.secretKey,
      passphrase:
        marketCodeForm.exchange === 'OKX' ? data.passphrase : undefined,
    });
  };

  const onDelete = useCallback(({ row }) => {
    setDeleteAlert({
      id: row.original.uuid,
      trade_config_uuid: row.original.trade_config_uuid,
      accessKey: row.original.access_key,
    });
  }, []);

  const columns = useMemo(
    () => [
      { accessorKey: 'registered_at', header: t('Registration'), size: 100 },
      { accessorKey: 'access_key', header: t('Access Key'), size: 120 },
      { accessorKey: 'secret_key', header: t('Secret Key'), size: 50 },
      { accessorKey: 'expires_at', header: t('Expiry'), size: 100 },
      {
        accessorKey: 'icon',
        enableGlobalFilter: false,
        enableSorting: false,
        size: 11,
        maxSize: 11,
        cell: renderActionIconCell,
        header: <span />,
      },
    ],
    [i18n.language]
  );

  const tableData = useMemo(
    () => ({
      target:
        exchangeApiKeys
          ?.filter(
            (item) => item.market_code === marketCodeCombination.target.value
          )
          .map((item) => ({
            ...item,
            registered_at: DateTime.fromISO(
              item.registered_datetime
            ).toLocaleString(DateTime.DATETIME_MED),
            access_key: truncate(item.access_key, { length: 40 }),
            secret_key: '●●●●●●',
          })) || [],
      origin:
        exchangeApiKeys
          ?.filter(
            (item) => item.market_code === marketCodeCombination.origin.value
          )
          .map((item) => ({
            ...item,
            registered_at: DateTime.fromISO(
              item.registered_datetime
            ).toLocaleString(DateTime.DATETIME_MED),
            access_key: truncate(item.access_key, { length: 40 }),
            secret_key: '●●●●●●',
          })) || [],
    }),
    [marketCodeCombination, exchangeApiKeys]
  );

  useEffect(() => {
    if (!marketCodeForm) {
      reset();
      setShowPassphrase(false);
      setShowSecretKey(false);
    }
  }, [marketCodeForm]);

  useEffect(() => {
    if (createResults.isSuccess) {
      reset();
      setShowPassphrase(false);
      setShowSecretKey(false);
      setMarketCodeForm(null);
    }
  }, [createResults]);

  useEffect(() => {
    if (deleteResults.isSuccess) setDeleteAlert(null);
  }, [deleteResults]);

  if (marketCodeCombination.value === 'ALL') return null;

  return (
    <Box sx={{ my: 2 }}>
      <Grid container spacing={3} sx={{ px: { xs: 2, md: 4 } }}>
        <Grid item md={6} xs={12}>
          <Typography align="center">
            {marketCodeCombination.target.icon}{' '}
            {marketCodeCombination.target.getLabel()}
            <IconButton
              color="success"
              onClick={() => setMarketCodeForm(marketCodeCombination.target)}
              sx={{ ml: 2, p: 0 }}
            >
              <AddIcon />
            </IconButton>
          </Typography>
          <ReactTableUI
            columns={columns}
            data={tableData.target}
            getHeaderProps={() => ({ sx: { textAlign: 'center' } })}
            getTableProps={() => ({ sx: { mt: 2 } })}
          />
        </Grid>
        <Grid item md={6} xs={12}>
          <Typography align="center">
            {marketCodeCombination.origin.icon}{' '}
            {marketCodeCombination.origin.getLabel()}
            <IconButton
              color="success"
              onClick={() => setMarketCodeForm(marketCodeCombination.origin)}
              sx={{ ml: 2, p: 0 }}
            >
              <AddIcon />
            </IconButton>
          </Typography>
          <ReactTableUI
            columns={columns}
            data={tableData.origin}
            options={{
              meta: {
                action: {
                  icon: DeleteIcon,
                  iconProps: { color: 'secondary' },
                  onClick: onDelete,
                },
              },
            }}
            getCellProps={() => ({
              sx: { py: 1, textAlign: 'center', wordWrap: 'break-word' },
            })}
            getHeaderProps={() => ({ sx: { textAlign: 'center' } })}
            getTableProps={() => ({ sx: { mt: 2 } })}
          />
        </Grid>
      </Grid>
      <Dialog
        fullWidth
        maxWidth="sm"
        open={!!marketCodeForm}
        onClose={handleCloseDialog}
        PaperProps={{
          autoComplete: 'off',
          component: 'form',
          onSubmit: handleSubmit(onSubmit),
        }}
      >
        <DialogTitle>
          {marketCodeForm?.icon} {marketCodeForm?.getLabel()} {t('API Key')}
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            {t(
              'To receive trade notifications, please enter your {{marketCode}} API Key',
              { marketCode: marketCodeForm?.getLabel() || '' }
            )}
            .
          </DialogContentText>
          <Controller
            name="accessKey"
            control={control}
            rules={{ required: true }}
            render={({ field, fieldState }) => (
              <TextField
                autoFocus
                fullWidth
                required
                margin="dense"
                variant="standard"
                label={t('Access Key')}
                error={!!fieldState.error}
                {...field}
              />
            )}
          />
          <Controller
            name="secretKey"
            control={control}
            rules={{ required: true }}
            render={({ field, fieldState }) => (
              <TextField
                fullWidth
                required
                margin="dense"
                variant="standard"
                label={t('Secret Key')}
                error={!!fieldState.error}
                type={showSecretKey ? 'text' : 'password'}
                InputProps={{
                  inputProps: { autoComplete: 'off' },
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle secret key visibility"
                        color="secondary"
                        onClick={() => setShowSecretKey((state) => !state)}
                        sx={{ p: 0 }}
                      >
                        {showSecretKey ? (
                          <VisibilityOffIcon />
                        ) : (
                          <VisibilityIcon />
                        )}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
                {...field}
              />
            )}
          />
          {marketCodeForm?.exchange === 'OKX' && (
            <Controller
              name="passphrase"
              control={control}
              rules={{ required: true }}
              render={({ field, fieldState }) => (
                <TextField
                  fullWidth
                  required
                  margin="dense"
                  variant="standard"
                  label={t('Passphrase')}
                  error={!!fieldState.error}
                  type={showPassphrase ? 'text' : 'password'}
                  InputProps={{
                    inputProps: { autoComplete: 'off' },
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          aria-label="toggle passphrase visibility"
                          color="secondary"
                          onClick={() => setShowPassphrase((state) => !state)}
                          sx={{ p: 0 }}
                        >
                          {showPassphrase ? (
                            <VisibilityOffIcon />
                          ) : (
                            <VisibilityIcon />
                          )}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                  {...field}
                />
              )}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button
            disabled={createResults.isLoading}
            onClick={handleCloseDialog}
          >
            {t('Cancel')}
          </Button>
          <Button type="submit" disabled={!isValid || createResults.isLoading}>
            {t('Register')}
          </Button>
        </DialogActions>
      </Dialog>
      <DeleteAlert
        loading={deleteResults.isLoading}
        open={!!deleteAlert}
        title={t(
          'Are you sure you want to permanently delete [{{accessKey}}...] API Key?',
          { accessKey: deleteAlert?.accessKey.substring(0, 6) }
        )}
        onCancel={() => setDeleteAlert(null)}
        onClose={() =>
          setDeleteAlert((state) => (deleteResults.isLoading ? state : null))
        }
        onDelete={() => deleteExchangeApiKey(deleteAlert)}
      />
    </Box>
  );
}
