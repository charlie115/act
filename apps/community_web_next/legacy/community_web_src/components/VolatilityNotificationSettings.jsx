import React, { useCallback, useEffect, useMemo, useState } from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Checkbox from '@mui/material/Checkbox';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';

import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import SyncAltIcon from '@mui/icons-material/SyncAlt';
import Switch from '@mui/material/Switch';

import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import { useTranslation } from 'react-i18next';
import { useForm, Controller } from 'react-hook-form';

import {
  useGetVolatilityNotificationsQuery,
  useCreateVolatilityNotificationMutation,
  useUpdateVolatilityNotificationMutation,
  useDeleteVolatilityNotificationMutation,
  useGetMarketCodesQuery,
} from 'redux/api/drf/infocore';

import ReactTableUI from 'components/ReactTableUI';
import DeleteAlert from 'components/DeleteAlert';

import { MARKET_CODE_LIST } from 'constants/lists';

// Cell renderers outside component
const renderSelectHeader = ({ table }) => (
  <Checkbox
    checked={table.getIsAllRowsSelected()}
    indeterminate={table.getIsSomeRowsSelected()}
    onChange={table.getToggleAllRowsSelectedHandler()}
    onClick={(e) => e.stopPropagation()}
  />
);

const renderSelectCell = ({ row }) => (
  <Checkbox
    checked={row.getIsSelected()}
    indeterminate={row.getIsSomeSelected()}
    onChange={row.getToggleSelectedHandler()}
    onClick={(e) => e.stopPropagation()}
  />
);

const renderMarketCodesCell = ({ row }) => {
  const target = MARKET_CODE_LIST.find(
    mc => mc.value === row.original.target_market_code
  );
  const origin = MARKET_CODE_LIST.find(
    mc => mc.value === row.original.origin_market_code
  );
  return (
    <Stack direction="row" spacing={0.5} alignItems="center">
      {target && (
        <Box
          component="img"
          src={target.icon}
          alt={target.getLabel()}
          sx={{ height: 16, width: 16 }}
        />
      )}
      <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>{target?.getLabel()}</Typography>
      <SyncAltIcon fontSize="small" color="secondary" />
      {origin && (
        <Box
          component="img"
          src={origin.icon}
          alt={origin.getLabel()}
          sx={{ height: 16, width: 16 }}
        />
      )}
      <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>{origin?.getLabel()}</Typography>
    </Stack>
  );
};

const renderThresholdCell = ({ getValue }) =>
  `${parseFloat(getValue()).toFixed(2)}`;

export default function VolatilityNotificationSettings({ marketCodeSelectorRef }) {
  const { t } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingConfig, setEditingConfig] = useState(null);
  const [rowSelection, setRowSelection] = useState({});
  const [deleteAlert, setDeleteAlert] = useState(false);

  const { data, isLoading } = useGetVolatilityNotificationsQuery();
  const { data: marketCodesData } = useGetMarketCodesQuery();
  const [createConfig, { isLoading: isCreating }] = useCreateVolatilityNotificationMutation();
  const [updateConfig, { isLoading: isUpdating }] = useUpdateVolatilityNotificationMutation();
  const [deleteConfig] = useDeleteVolatilityNotificationMutation();

  const { control, handleSubmit, reset, setValue } = useForm({
    defaultValues: {
      market_code_combination: '',
      volatility_threshold: 0.5,
      notification_interval_minutes: 180,
      enabled: true,
    },
  });

  const configs = useMemo(() => data?.results || [], [data]);

  const marketCodeCombinations = useMemo(() => {
    if (!marketCodesData) return [];

    const combinations = [];

    // Loop through each target market code and its active origins
    Object.entries(marketCodesData).forEach(([targetValue, originValues]) => {
      const target = MARKET_CODE_LIST.find((mc) => mc.value === targetValue);
      if (!target) return;

      // For each active origin, create a combination
      originValues.forEach((originValue) => {
        const origin = MARKET_CODE_LIST.find((mc) => mc.value === originValue);
        if (!origin) return;

        combinations.push({
          value: `${targetValue}:${originValue}`,
          target,
          origin,
        });
      });
    });

    return combinations;
  }, [marketCodesData]);

  const handleOpenDialog = (config = null) => {
    if (config) {
      setEditingConfig(config);
      setValue('market_code_combination', `${config.target_market_code}:${config.origin_market_code}`);
      setValue('volatility_threshold', parseFloat(config.volatility_threshold));
      setValue('notification_interval_minutes', config.notification_interval_minutes);
      setValue('enabled', config.enabled);
    } else {
      setEditingConfig(null);
      reset();
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingConfig(null);
    reset();
  };

  const onSubmit = async (formData) => {
    try {
      // eslint-disable-next-line camelcase
      const [target_market_code, origin_market_code] = formData.market_code_combination.split(':');
      const payload = {
        target_market_code, // eslint-disable-line camelcase
        origin_market_code, // eslint-disable-line camelcase
        volatility_threshold: formData.volatility_threshold,
        notification_interval_minutes: formData.notification_interval_minutes,
        enabled: formData.enabled,
      };

      if (editingConfig) {
        await updateConfig({ id: editingConfig.id, ...payload }).unwrap();
      } else {
        await createConfig(payload).unwrap();
      }
      handleCloseDialog();
    } catch (error) {
      console.error('Failed to save config:', error);
    }
  };

  const handleDelete = useCallback(async () => {
    const selectedIds = Object.keys(rowSelection).filter(key => rowSelection[key]);
    try {
      await Promise.all(selectedIds.map(id => deleteConfig(id)));
      setRowSelection({});
      setDeleteAlert(false);
    } catch (error) {
      console.error('Failed to delete configs:', error);
    }
  }, [rowSelection, deleteConfig]);

  const renderStatusCell = useCallback(({ row }) => {
    const config = row.original;

    const handleToggle = async (e) => {
      e.stopPropagation(); // Prevent row click
      const newEnabled = e.target.checked;

      try {
        await updateConfig({
          id: config.id,
          target_market_code: config.target_market_code,
          origin_market_code: config.origin_market_code,
          volatility_threshold: config.volatility_threshold,
          notification_interval_minutes: config.notification_interval_minutes,
          enabled: newEnabled,
        }).unwrap();
      } catch (error) {
        console.error('Failed to update config:', error);
      }
    };

    return (
      <Switch
        checked={config.enabled}
        onChange={handleToggle}
        onClick={(e) => e.stopPropagation()}
      />
    );
  }, [updateConfig]);

  const columns = useMemo(
    () => [
      {
        id: 'select',
        header: renderSelectHeader,
        cell: renderSelectCell,
        size: 40,
      },
      {
        accessorKey: 'market_codes',
        header: t('Market Codes'),
        cell: renderMarketCodesCell,
      },
      {
        accessorKey: 'volatility_threshold',
        header: t('Volatility Threshold'),
        cell: renderThresholdCell,
        size: 120,
      },
      {
        accessorKey: 'notification_interval_minutes',
        header: t('Interval (minutes)'),
        size: 100,
      },
      {
        accessorKey: 'enabled',
        header: t('Status'),
        cell: renderStatusCell,
        size: 80,
      },
    ],
    [t, renderStatusCell]
  );

  const selectedCount = Object.keys(rowSelection).filter(key => rowSelection[key]).length;

  return (
    <Box sx={{ p: 2 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
        <Typography variant="h6">{t('Volatility Notification Settings')}</Typography>
        <Stack direction="row" spacing={1}>
          {selectedCount > 0 && (
            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={() => setDeleteAlert(true)}
            >
              {t('Delete')} ({selectedCount})
            </Button>
          )}
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
          >
            {t('Add Configuration')}
          </Button>
        </Stack>
      </Stack>

      <ReactTableUI
        columns={columns}
        data={configs}
        options={{
          state: { rowSelection },
          onRowSelectionChange: setRowSelection,
          enableRowSelection: true,
          getRowId: (row) => row.id,
          initialState: {
            pagination: {
              pageSize: 9999,
            },
          },
        }}
        getRowProps={(row) => ({
          onClick: () => handleOpenDialog(row.original),
          style: { cursor: 'pointer' },
        })}
        loading={isLoading}
      />

      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingConfig ? t('Edit Configuration') : t('Add Configuration')}
        </DialogTitle>
        <DialogContent>
          <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ pt: 2 }}>
            <Stack spacing={2}>
              <Controller
                name="market_code_combination"
                control={control}
                rules={{ required: true }}
                render={({ field }) => (
                  <FormControl fullWidth>
                    <InputLabel>{t('Market Codes')}</InputLabel>
                    <Select {...field} label={t('Market Codes')}>
                      {marketCodeCombinations.map(combo => (
                        <MenuItem key={combo.value} value={combo.value}>
                          <Stack direction="row" spacing={0.5} alignItems="center">
                            <Box
                              component="img"
                              src={combo.target.icon}
                              alt={combo.target.getLabel()}
                              sx={{ height: 16, width: 16 }}
                            />
                            <Typography variant="body2">{combo.target.getLabel()}</Typography>
                            <SyncAltIcon fontSize="small" color="secondary" />
                            <Box
                              component="img"
                              src={combo.origin.icon}
                              alt={combo.origin.getLabel()}
                              sx={{ height: 16, width: 16 }}
                            />
                            <Typography variant="body2">{combo.origin.getLabel()}</Typography>
                          </Stack>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                )}
              />

              <Controller
                name="volatility_threshold"
                control={control}
                rules={{ required: true, min: 0 }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    type="number"
                    label={t('Volatility Threshold')}
                    inputProps={{ step: 0.1, min: 0 }}
                    fullWidth
                  />
                )}
              />

              <Controller
                name="notification_interval_minutes"
                control={control}
                rules={{ required: true, min: 1 }}
                render={({ field }) => (
                  <TextField
                    {...field}
                    type="number"
                    label={t('Notification Interval (minutes)')}
                    inputProps={{ step: 1, min: 1 }}
                    fullWidth
                  />
                )}
              />

              <Controller
                name="enabled"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth>
                    <InputLabel>{t('Status')}</InputLabel>
                    <Select
                      {...field}
                      label={t('Status')}
                      value={field.value ? 'true' : 'false'}
                      onChange={(e) => field.onChange(e.target.value === 'true')}
                    >
                      <MenuItem value="true">{t('Enabled')}</MenuItem>
                      <MenuItem value="false">{t('Disabled')}</MenuItem>
                    </Select>
                  </FormControl>
                )}
              />
            </Stack>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>{t('Cancel')}</Button>
          <Button
            onClick={handleSubmit(onSubmit)}
            variant="contained"
            disabled={isCreating || isUpdating}
          >
            {editingConfig ? t('Update') : t('Create')}
          </Button>
        </DialogActions>
      </Dialog>

      <DeleteAlert
        open={deleteAlert}
        onClose={() => setDeleteAlert(false)}
        onConfirm={handleDelete}
        title={t('Delete Configurations')}
        message={t('Are you sure you want to delete {{count}} configuration(s)?', { count: selectedCount })}
      />
    </Box>
  );
}
