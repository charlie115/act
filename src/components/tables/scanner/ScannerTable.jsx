import React, { useCallback, useEffect, useMemo, useState } from 'react';

import Box from '@mui/material/Box';
import _Paper from '@mui/material/Paper';
import _Table from '@mui/material/Table';
import _TableBody from '@mui/material/TableBody';
import _TableCell from '@mui/material/TableCell';
import _TableContainer from '@mui/material/TableContainer';
import _TableHead from '@mui/material/TableHead';
import _TableRow from '@mui/material/TableRow';
import Checkbox from '@mui/material/Checkbox';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import IconButton from '@mui/material/IconButton';
import SyncAltIcon from '@mui/icons-material/SyncAlt';
import DeleteIcon from '@mui/icons-material/Delete';
import _AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import TextField from '@mui/material/TextField';
import FormControlLabel from '@mui/material/FormControlLabel';
import _FormHelperText from '@mui/material/FormHelperText';
import InputAdornment from '@mui/material/InputAdornment';
import CircularProgress from '@mui/material/CircularProgress';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import Divider from '@mui/material/Divider';

import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import { useTranslation } from 'react-i18next';

// Common components
import ReactTableUI from 'components/ReactTableUI';
import DeleteAlert from 'components/DeleteAlert';

// Utility functions
import _formatIntlNumber from 'utils/formatIntlNumber';

// Common table components
import renderCurrencyFormatCell from 'components/tables/common/renderCurrencyFormatCell';
import renderDateCell from 'components/tables/common/renderDateCell';
import renderExpandCell from 'components/tables/common/renderExpandCell';

// Reuse components from trigger table
import renderSelectHeader from 'components/tables/trigger/renderSelectHeader';
import renderSelectCell from 'components/tables/trigger/renderSelectCell';
import renderMarketCodesCell from 'components/tables/trigger/renderMarketCodesCell';

// API hooks
import { 
  useGetAllTriggerScannersQuery, 
  useDeleteMultipleTriggerScannerMutation,
  usePostTriggerScannerMutation,
  usePutTriggerScannerMutation,
} from 'redux/api/drf/tradecore';

import { useGetAssetsQuery } from 'redux/api/drf/infocore';

// Import TriggersTable
import TriggersTable from 'components/tables/trigger/TriggersTable';

// Scanner-specific cell renderers
import { renderAtpCell, renderFundingRateCell, renderIterationCell, renderIntervalCell, renderScannerValueCell } from './renderCells';

export default function ScannerTable({ marketCodeCombination, _queryKey, tradeConfigAllocations, tradeConfigUuids }) {
  const { t } = useTranslation();
  const tableRef = React.useRef();
  
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // State management
  const [rowSelection, setRowSelection] = useState({});
  const [deleteAlert, setDeleteAlert] = useState(false);
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 100 });
  const [expanded, setExpanded] = useState({});
  const [showAddForm, setShowAddForm] = useState(false);
  const [displayTriggers, setDisplayTriggers] = useState(false);
  
  // Get API data
  const { data: scannerData = [], isLoading } = useGetAllTriggerScannersQuery(
    { tradeConfigUuids }, 
    { pollingInterval: 1000 * 1, skip: !tradeConfigUuids?.length }
  );
  
  // API hooks
  const { data: assetsData } = useGetAssetsQuery();
  
  // Delete mutation
  const [deleteMultipleTriggerScanner, { isLoading: isDeleteLoading }] = useDeleteMultipleTriggerScannerMutation();
  
  // API mutations
  const [postTriggerScanner, { isLoading: _isAddLoading }] = usePostTriggerScannerMutation();

  // Reset selection when data changes
  useEffect(() => {
    setRowSelection({});
  }, [scannerData]);

  const getRowId = useCallback((row) => row.uuid, []);
  
  // Auto-expand the new scanner row when add button is clicked
  useEffect(() => {
    if (showAddForm && tableRef.current) {
      // Use a longer timeout to ensure the row is rendered before trying to expand it
      setTimeout(() => {
        // Try to find the row by ID - only use getRowById which is the proper API method
        if (tableRef.current.getRowById) {
          const addRow = tableRef.current.getRowById('add-scanner');
          if (addRow) {
            addRow.toggleExpanded(true);
          }
        }
        
        // If the row wasn't found or expanded, manually set the expanded state
        if (!Object.keys(expanded || {}).includes('add-scanner')) {
          setExpanded({ 'add-scanner': true });
        }
      }, 300); // Increased timeout to give table more time to render
    }
  }, [showAddForm, expanded]);

  // Handle row expansion
  const onExpandedChange = useCallback((newExpanded) => {
    // Close the "add" row when another row is expanded or when add row is collapsed
    const currentExpandedId = Object.keys(expanded || {})[0];
    const newExpandedId = Object.keys(newExpanded || {})[0];
    
    if (currentExpandedId === 'add-scanner' && !newExpandedId) {
      setShowAddForm(false);
    }
    
    // Reset triggers display when no row is expanded or different row is expanded
    if (!newExpandedId || currentExpandedId !== newExpandedId) {
      setDisplayTriggers(false);
    }
    
    setExpanded(newExpanded);
  }, [expanded]);

  // Define columns
  const columns = useMemo(() => [
    {
      accessorKey: 'select',
      enableGlobalFilter: false,
      enableSorting: false,
      size: isMobile ? 5 : 10,
      header: renderSelectHeader,
      cell: renderSelectCell,
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
      header: t('Entry'),
      cell: renderScannerValueCell,
    },
    {
      accessorKey: 'exit',
      size: isMobile ? 27 : 80,
      header: t('Exit'),
      cell: renderScannerValueCell,
    },
    {
      accessorKey: 'tradeCapital',
      size: isMobile ? 29 : 80,
      header: t('Trade Capital'),
      cell: renderCurrencyFormatCell,
    },
    {
      accessorKey: 'minTargetAtp',
      size: isMobile ? 29 : 80,
      header: t('Minimum Trading Volume'),
      cell: renderAtpCell,
    },
    {
      accessorKey: 'minOriginFundingRate',
      size: isMobile ? 29 : 80,
      header: t('Minimum Funding Rate'),
      cell: renderFundingRateCell,
    },
    {
      accessorKey: 'currentIteration',
      size: isMobile ? 25 : 60,
      header: t('Current Iteration'),
      cell: renderIterationCell,
    },
    {
      accessorKey: 'maxIteration',
      size: isMobile ? 25 : 60,
      header: t('Maximum Iteration'),
      cell: renderIterationCell,
    },
    {
      accessorKey: 'iterationInterval',
      size: isMobile ? 25 : 60,
      header: t('Iteration Interval'),
      cell: renderIntervalCell,
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
  ], [marketCodeCombination, isMobile, t]);

  // Transform data for the table
  const tableData = useMemo(() => {
    const tempItems = [];
    
    // Add the "Create new scanner" row when showAddForm is true
    if (showAddForm && marketCodeCombination && marketCodeCombination.value !== 'ALL') {
      // Extract icon URLs from market code combination
      const targetIconElement = marketCodeCombination?.target?.icon;
      const originIconElement = marketCodeCombination?.origin?.icon;
      const targetIconUrl = typeof targetIconElement === 'string' ? 
        targetIconElement : targetIconElement?.props?.src;
      const originIconUrl = typeof originIconElement === 'string' ? 
        originIconElement : originIconElement?.props?.src;
      
      // Use a proper UUID format for the add-scanner row
      tempItems.push({
        uuid: 'add-scanner',
        id: 'add-scanner', // Add id property as fallback
        add: true,
        marketCodes: {
          targetMarketCode: marketCodeCombination?.target?.value,
          originMarketCode: marketCodeCombination?.origin?.value,
        },
        targetMarketIcon: targetIconUrl,
        originMarketIcon: originIconUrl,
        entry: null,
        exit: null,
        tradeCapital: null,
        minTargetAtp: null,
        minOriginFundingRate: null,
        currentIteration: null,
        maxIteration: null,
        iterationInterval: null,
        created: null,
      });
    }
    
    // Add existing scanner data
    const filteredScannerData = scannerData
      .filter(item => {
        if (!item) return false;
        
        // Filter by market code combination
        const marketMatch = !marketCodeCombination || 
                           marketCodeCombination.value === 'ALL' || 
                           marketCodeCombination?.tradeConfigUuid === item.trade_config_uuid;
        
        return marketMatch;
      })
      .map(item => {
        // Find the appropriate trade config allocation for this scanner item
        const tradeConfig = tradeConfigAllocations.find(
          (o) => o.uuid === item.trade_config_uuid
        );
        
        // Extract market icons properly, handling both string URLs and React elements
        const targetIconElement = tradeConfig?.target?.icon || marketCodeCombination?.target?.icon;
        const originIconElement = tradeConfig?.origin?.icon || marketCodeCombination?.origin?.icon;
        
        // Handle both direct string URLs and React elements with src props
        const targetIconUrl = typeof targetIconElement === 'string' ? 
          targetIconElement : targetIconElement?.props?.src;
        const originIconUrl = typeof originIconElement === 'string' ? 
          originIconElement : originIconElement?.props?.src;
        
        return {
          ...item,
          marketCodes: {
            targetMarketCode: tradeConfig?.target?.value || marketCodeCombination?.target?.value,
            originMarketCode: tradeConfig?.origin?.value || marketCodeCombination?.origin?.value,
          },
          entry: item.low,
          exit: item.high,
          tradeCapital: item.trade_capital,
          minTargetAtp: item.min_target_atp,
          minOriginAtp: item.min_origin_atp,
          minTargetFundingRate: item.min_target_funding_rate,
          minOriginFundingRate: item.min_origin_funding_rate,
          currentIteration: item.curr_repeat_num,
          maxIteration: item.max_repeat_num,
          iterationInterval: item.repeat_term_secs,
          created: item.registered_datetime,
          targetMarketIcon: targetIconUrl,
          originMarketIcon: originIconUrl,
          icon: assetsData?.[item.base_asset]?.icon,
        };
      });
    
    return [...tempItems, ...filteredScannerData];
  }, [scannerData, marketCodeCombination, tradeConfigAllocations, showAddForm, assetsData]);


  
  // Form submission handler for new scanner
  const handleAddScanner = useCallback(async (formData) => {
    try {
      await postTriggerScanner({
        ...formData,
        trade_config_uuid: marketCodeCombination?.tradeConfigUuid
      }).unwrap();
      setShowAddForm(false);
      return { success: true };
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('Failed to add scanner:', error);
      return { error };
    }
  }, [postTriggerScanner, marketCodeCombination]);

  // Handle delete function
  const handleDelete = useCallback(() => {
    const selectedItems = Object.keys(rowSelection).map(uuid => {
      const details = tableData.find((o) => o.uuid === uuid);
      return {
        uuid,
        params: { tradeConfigUuid: details?.trade_config_uuid }
      };
    });
    
    deleteMultipleTriggerScanner(selectedItems)
      .unwrap()
      .then(() => {
        setRowSelection({});
        setDeleteAlert(false);
      })
      .catch(error => {
        // eslint-disable-next-line no-console
        console.error('Failed to delete scanner items:', error);
        setDeleteAlert(false);
      });
  }, [deleteMultipleTriggerScanner, rowSelection, tableData]);

  // Render sub-component for expanded rows
  const renderSubComponent = useCallback(({ row: { original, toggleExpanded } }) => {
    if (original.add) {
      // Render add form for new scanner
      return (
        <Box sx={{ p: 2, bgcolor: 'background.default' }}>
          <ScannerForm
            onSubmit={handleAddScanner}
            onCancel={() => setShowAddForm(false)}
          />
        </Box>
      );
    }
    
    // Render edit form for existing scanner
    return (
      <Box sx={{ bgcolor: 'background.default', pt: 1 }}>
        <Box sx={{ ml: 3, mb: 1 }}>
          <Button
            color="info"
            size="small"
            endIcon={
              displayTriggers ? (
                <VisibilityOffIcon size="small" />
              ) : (
                <VisibilityIcon size="small" />
              )
            }
            onClick={() => setDisplayTriggers((state) => !state)}
          >
            {displayTriggers
              ? t('Hide Spawned Triggers')
              : t('Show Spawned Triggers')}
          </Button>
        </Box>
        {displayTriggers && (
          <Box sx={{ px: 2 }}>
            <TriggersTable
              marketCodeCombination={marketCodeCombination}
              queryKey={_queryKey}
              tradeConfigAllocations={tradeConfigAllocations}
              tradeConfigUuids={tradeConfigUuids}
              triggerScannerUuid={original.uuid}
              scannerTradeConfigUuid={original.trade_config_uuid}
            />
          </Box>
        )}
        <Divider />
        <Box sx={{ p: 2, bgcolor: 'background.default' }}>
          <UpdateScannerForm
            _defaultLow={original.entry}
            _defaultHigh={original.exit}
            _defaultTradeCapital={original.tradeCapital}
            _defaultMinTargetAtp={original.minTargetAtp}
            _defaultMinOriginFundingRate={original.minOriginFundingRate}
            _defaultMaxRepeatNum={original.maxIteration}
            _defaultRepeatTermSecs={original.iterationInterval}
            _tradeConfigUuid={original.trade_config_uuid}
            _uuid={original.uuid}
            toggleExpanded={toggleExpanded}
          />
        </Box>
      </Box>
    );
  }, [handleAddScanner, displayTriggers, marketCodeCombination, _queryKey, tradeConfigAllocations, tradeConfigUuids, t]);

  return (
    <Box sx={{ mx: { xs: 0, md: 1 }, p: { xs: 0, md: 1 } }}>
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        spacing={1}
        sx={{ mb: 2 }}
      >
        <Stack direction="row" spacing={1}>
          {/* Add any other controls here */}
        </Stack>
        
        <Box
          className={
            marketCodeCombination &&
            marketCodeCombination.value !== 'ALL' &&
            !marketCodeCombination.tradeConfigUuid
              ? 'animate__animated animate__pulse animate__repeat-2'
              : undefined
          }
        >
          <Button
            variant="contained"
            onClick={() => {
              setShowAddForm(true);
              // Directly set the expanded state when button is clicked
              setExpanded({ 'add-scanner': true });
            }}
            disabled={!marketCodeCombination || marketCodeCombination.value === 'ALL'}
          >
            {t('Add Scanner')}
          </Button>
        </Box>
      </Stack>
      
      {Object.keys(rowSelection).length > 0 && (
        <Stack alignItems="center" direction="row" spacing={2} sx={{ mb: 2 }}>
          <Typography sx={{ fontWeight: 700 }}>
            {t('{{selected}} of {{total}} selected', {
              selected: Object.keys(rowSelection).length,
              total: scannerData?.length,
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
        options={{
          getRowId,
          enableRowSelection: true,
          state: { pagination, rowSelection, expanded },
          onPaginationChange: setPagination,
          onRowSelectionChange: setRowSelection,
          onExpandedChange,
          meta: {
            theme,
            isMobile,
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
      
      <DeleteAlert
        loading={isDeleteLoading}
        open={deleteAlert}
        title={t(
          'Are you sure you want to permanently delete the selected scanner items?'
        )}
        onCancel={() => setDeleteAlert(false)}
        onClose={() => setDeleteAlert(isDeleteLoading)}
        onDelete={handleDelete}
      />
    </Box>
  );
}

// Scanner Form Component
function ScannerForm({ onSubmit, onCancel }) {
  const { t } = useTranslation();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  
  const [formState, setFormState] = useState({
    low: '',
    high: '',
    min_target_atp: '',
    enableMinTargetAtp: true,
    min_origin_funding_rate: '',
    enableMinOriginFundingRate: true,
    trade_capital: '',
    max_repeat_num: 1,
    repeat_term_secs: 300,
  });
  
  const [formErrors, setFormErrors] = useState({});
  
  const handleFormChange = useCallback((e) => {
    const { name, value, type, checked } = e.target;
    
    if (type === 'checkbox') {
      setFormState(prev => ({ ...prev, [name]: checked }));
    } else {
      setFormState(prev => {
        const newState = { ...prev, [name]: value };
        
        // Real-time validation for Entry/Exit values
        if (name === 'low' || name === 'high') {
          const lowValue = name === 'low' ? value : prev.low;
          const highValue = name === 'high' ? value : prev.high;
          
          // Only validate if both values exist
          if (lowValue && highValue) {
            if (parseFloat(lowValue) >= parseFloat(highValue)) {
              setFormErrors(errors => ({
                ...errors,
                low: t('Entry must be lower than exit'),
                high: t('Exit must be higher than entry')
              }));
            } else {
              // Clear errors if validation passes
              setFormErrors(errors => ({
                ...errors,
                low: undefined,
                high: undefined
              }));
            }
          }
        } else if (formErrors[name]) {
          // Clear the error for this field if any
          setFormErrors(currentErrors => ({
            ...currentErrors,
            [name]: undefined
          }));
        }
        
        return newState;
      });
    }
    
    // Clear the error for non-Entry/Exit fields
    if (name !== 'low' && name !== 'high' && formErrors[name]) {
      setFormErrors(currentErrors => ({ ...currentErrors, [name]: undefined }));
    }
  }, [formErrors, t]);
  
  const validateForm = useCallback(() => {
    const errors = {};
    
    // Required fields
    if (!formState.low) errors.low = t('This field is required');
    if (!formState.high) errors.high = t('This field is required');
    if (!formState.trade_capital) errors.trade_capital = t('This field is required');
    else if (parseInt(formState.trade_capital, 10) < 10000) errors.trade_capital = t('Minimum value is 10000');
    
    // Numeric validations
    if (formState.min_target_atp && formState.enableMinTargetAtp && Number.isNaN(Number(formState.min_target_atp))) {
      errors.min_target_atp = t('Must be a number');
    }
    
    if (formState.min_origin_funding_rate && formState.enableMinOriginFundingRate && Number.isNaN(Number(formState.min_origin_funding_rate))) {
      errors.min_origin_funding_rate = t('Must be a number');
    }
    
    if (formState.max_repeat_num && (Number.isNaN(Number(formState.max_repeat_num)) || parseInt(formState.max_repeat_num, 10) < 1)) {
      errors.max_repeat_num = t('Must be a positive number');
    }
    
    if (formState.repeat_term_secs && (Number.isNaN(Number(formState.repeat_term_secs)) || parseInt(formState.repeat_term_secs, 10) < 1)) {
      errors.repeat_term_secs = t('Must be a positive number');
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  }, [formState, t]);
  
  const handleSubmit = useCallback(async () => {
    if (!validateForm()) return;
    
    setIsSubmitting(true);
    setError(null);
    
    // Prepare the data for submission
    const payload = {
      low: parseFloat(formState.low),
      high: parseFloat(formState.high),
      trade_capital: parseInt(formState.trade_capital, 10),
      max_repeat_num: parseInt(formState.max_repeat_num, 10),
      repeat_term_secs: parseInt(formState.repeat_term_secs, 10),
    };
    
    // Optional fields
    if (formState.enableMinTargetAtp && formState.min_target_atp) {
      // Multiply by 100,000,000 as per requirements
      payload.min_target_atp = parseFloat(formState.min_target_atp) * 100000000;
    }
    
    if (formState.enableMinOriginFundingRate && formState.min_origin_funding_rate) {
      // Divide by 100 to convert percentage to decimal value
      payload.min_origin_funding_rate = parseFloat(formState.min_origin_funding_rate) / 100;
    }
    
    try {
      const result = await onSubmit(payload);
      
      if (result.error) {
        // Handle API errors
        if (result.error.data?.detail) {
          setError(result.error.data.detail);
        } else if (result.error.data) {
          // Map backend validation errors to form fields
          const backendErrors = {};
          Object.entries(result.error.data).forEach(([key, value]) => {
            backendErrors[key] = Array.isArray(value) ? value[0] : value;
          });
          setFormErrors(prev => ({ ...prev, ...backendErrors }));
        }
      }
    } finally {
      setIsSubmitting(false);
    }
  }, [formState, validateForm, onSubmit]);
  
  return (
    <Box sx={{ maxWidth: 700, mx: 'auto' }}>
      {error && (
        <Typography color="error" variant="body2" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}
      
      <Box sx={{ mt: 1 }}>
        {/* Entry/Exit Values - Two columns */}
        <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
          <TextField
            label={t('Entry')}
            name="low"
            value={formState.low}
            onChange={handleFormChange}
            variant="outlined"
            type="number"
            size="small"
            fullWidth
            required
            error={!!formErrors.low}
            helperText={formErrors.low}
            inputProps={{ step: "0.001" }}
            disabled={isSubmitting}
          />
          
          <TextField
            label={t('Exit')}
            name="high"
            value={formState.high}
            onChange={handleFormChange}
            variant="outlined"
            type="number"
            size="small"
            fullWidth
            required
            error={!!formErrors.high}
            helperText={formErrors.high}
            inputProps={{ step: "0.001" }}
            disabled={isSubmitting}
          />
        </Stack>
        
        {/* Trade Capital */}
        <TextField
          label={t('Trade Capital')}
          name="trade_capital"
          value={formState.trade_capital}
          onChange={handleFormChange}
          variant="outlined"
          type="number"
          size="small"
          fullWidth
          required
          error={!!formErrors.trade_capital}
          helperText={formErrors.trade_capital || t('Minimum value is 10000')}
          disabled={isSubmitting}
          sx={{ mb: 2 }}
        />
        
        {/* Min Trading Volume with checkbox and field in the same row */}
        <Box sx={{ mb: 2 }}>
          <FormControlLabel
            control={
              <Checkbox
                checked={formState.enableMinTargetAtp}
                onChange={handleFormChange}
                name="enableMinTargetAtp"
                disabled={isSubmitting}
                size="small"
              />
            }
            label={t('Enable Minimum Trading Volume')}
          />
          
          <TextField
            label={t('Minimum Trading Volume')}
            name="min_target_atp"
            value={formState.min_target_atp}
            onChange={handleFormChange}
            variant="outlined"
            type="number"
            size="small"
            fullWidth
            disabled={!formState.enableMinTargetAtp || isSubmitting}
            error={!!formErrors.min_target_atp}
            helperText={formErrors.min_target_atp}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  {t('100M')}
                </InputAdornment>
              ),
            }}
          />
        </Box>
        
        {/* Min Funding Rate with checkbox and field in the same row */}
        <Box sx={{ mb: 2 }}>
          <FormControlLabel
            control={
              <Checkbox
                checked={formState.enableMinOriginFundingRate}
                onChange={handleFormChange}
                name="enableMinOriginFundingRate"
                disabled={isSubmitting}
                size="small"
              />
            }
            label={t('Enable Minimum Funding Rate')}
          />
          
          <TextField
            label={t('Minimum Funding Rate')}
            name="min_origin_funding_rate"
            value={formState.min_origin_funding_rate}
            onChange={handleFormChange}
            variant="outlined"
            type="number"
            size="small"
            fullWidth
            disabled={!formState.enableMinOriginFundingRate || isSubmitting}
            error={!!formErrors.min_origin_funding_rate}
            helperText={formErrors.min_origin_funding_rate}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  %
                </InputAdornment>
              ),
            }}
          />
        </Box>
        
        {/* Max Iteration and Interval in a row */}
        <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
          <TextField
            label={t('Maximum Iteration')}
            name="max_repeat_num"
            value={formState.max_repeat_num}
            onChange={handleFormChange}
            variant="outlined"
            type="number"
            size="small"
            fullWidth
            required
            error={!!formErrors.max_repeat_num}
            helperText={formErrors.max_repeat_num}
            disabled={isSubmitting}
            inputProps={{ min: "1" }}
          />
          
          <TextField
            label={t('Registration Interval (seconds)')}
            name="repeat_term_secs"
            value={formState.repeat_term_secs}
            onChange={handleFormChange}
            variant="outlined"
            type="number"
            size="small"
            fullWidth
            required
            error={!!formErrors.repeat_term_secs}
            helperText={formErrors.repeat_term_secs}
            disabled={parseInt(formState.max_repeat_num, 10) === 1 || isSubmitting}
            inputProps={{ min: "1" }}
          />
        </Stack>
        
        <Stack direction="row" spacing={2} justifyContent="flex-end">
          <Button 
            onClick={onCancel} 
            disabled={isSubmitting}
            size="small"
          >
            {t('Cancel')}
          </Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained" 
            disabled={isSubmitting}
            size="small"
            startIcon={isSubmitting ? <CircularProgress size={16} /> : null}
          >
            {t('Register')}
          </Button>
        </Stack>
      </Box>
    </Box>
  );
}

// Replace the UpdateScannerForm component at the bottom of the file
function UpdateScannerForm({ 
  _defaultLow, 
  _defaultHigh, 
  _defaultTradeCapital, 
  _defaultMinTargetAtp, 
  _defaultMinOriginFundingRate,
  _defaultMaxRepeatNum,
  _defaultRepeatTermSecs,
  _tradeConfigUuid, 
  _uuid, 
  toggleExpanded 
}) {
  const { t } = useTranslation();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  
  // Initialize form state with default values
  const [formState, setFormState] = useState({
    low: _defaultLow || '',
    high: _defaultHigh || '',
    min_target_atp: _defaultMinTargetAtp ? (_defaultMinTargetAtp / 100000000) : '', // Convert from backend format
    enableMinTargetAtp: !!_defaultMinTargetAtp,
    min_origin_funding_rate: _defaultMinOriginFundingRate ? (_defaultMinOriginFundingRate * 100) : '', // Convert from decimal to percentage
    enableMinOriginFundingRate: !!_defaultMinOriginFundingRate,
    trade_capital: _defaultTradeCapital || '',
    max_repeat_num: _defaultMaxRepeatNum || 1,
    repeat_term_secs: _defaultRepeatTermSecs || 300,
  });
  
  const [formErrors, setFormErrors] = useState({});
  
  // Use the put mutation
  const [putTriggerScanner, { isLoading: isUpdateLoading }] = usePutTriggerScannerMutation();
  
  const handleFormChange = useCallback((e) => {
    const { name, value, type, checked } = e.target;
    
    if (type === 'checkbox') {
      setFormState(prev => ({ ...prev, [name]: checked }));
    } else {
      setFormState(prev => {
        const newState = { ...prev, [name]: value };
        
        // Real-time validation for Entry/Exit values
        if (name === 'low' || name === 'high') {
          const lowValue = name === 'low' ? value : prev.low;
          const highValue = name === 'high' ? value : prev.high;
          
          // Only validate if both values exist
          if (lowValue && highValue) {
            if (parseFloat(lowValue) >= parseFloat(highValue)) {
              setFormErrors(errors => ({
                ...errors,
                low: t('Entry must be lower than exit'),
                high: t('Exit must be higher than entry')
              }));
            } else {
              // Clear errors if validation passes
              setFormErrors(errors => ({
                ...errors,
                low: undefined,
                high: undefined
              }));
            }
          }
        } else if (formErrors[name]) {
          // Clear the error for this field if any
          setFormErrors(currentErrors => ({
            ...currentErrors,
            [name]: undefined
          }));
        }
        
        return newState;
      });
    }
    
    // Clear the error for non-Entry/Exit fields
    if (name !== 'low' && name !== 'high' && formErrors[name]) {
      setFormErrors(currentErrors => ({ ...currentErrors, [name]: undefined }));
    }
  }, [formErrors, t]);
  
  const validateForm = useCallback(() => {
    const errors = {};
    
    // Required fields
    if (!formState.low) errors.low = t('This field is required');
    if (!formState.high) errors.high = t('This field is required');
    if (!formState.trade_capital) errors.trade_capital = t('This field is required');
    else if (parseInt(formState.trade_capital, 10) < 10000) errors.trade_capital = t('Minimum value is 10000');
    
    // Numeric validations
    if (formState.min_target_atp && formState.enableMinTargetAtp && Number.isNaN(Number(formState.min_target_atp))) {
      errors.min_target_atp = t('Must be a number');
    }
    
    if (formState.min_origin_funding_rate && formState.enableMinOriginFundingRate && Number.isNaN(Number(formState.min_origin_funding_rate))) {
      errors.min_origin_funding_rate = t('Must be a number');
    }
    
    if (formState.max_repeat_num && (Number.isNaN(Number(formState.max_repeat_num)) || parseInt(formState.max_repeat_num, 10) < 1)) {
      errors.max_repeat_num = t('Must be a positive number');
    }
    
    if (formState.repeat_term_secs && (Number.isNaN(Number(formState.repeat_term_secs)) || parseInt(formState.repeat_term_secs, 10) < 1)) {
      errors.repeat_term_secs = t('Must be a positive number');
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  }, [formState, t]);
  
  const handleSubmit = useCallback(async () => {
    if (!validateForm()) return;
    
    setIsSubmitting(true);
    setError(null);
    // Prepare the data for submission
    const payload = {
      uuid: _uuid,
      low: parseFloat(formState.low),
      high: parseFloat(formState.high),
      trade_capital: parseInt(formState.trade_capital, 10),
      max_repeat_num: parseInt(formState.max_repeat_num, 10),
      repeat_term_secs: parseInt(formState.repeat_term_secs, 10),
      trade_config_uuid: _tradeConfigUuid,
    };
    
    // Optional fields
    if (formState.enableMinTargetAtp && formState.min_target_atp) {
      // Multiply by 100,000,000 as per requirements
      payload.min_target_atp = parseFloat(formState.min_target_atp) * 100000000;
    }
    
    if (formState.enableMinOriginFundingRate && formState.min_origin_funding_rate) {
      // Divide by 100 to convert percentage to decimal value
      payload.min_origin_funding_rate = parseFloat(formState.min_origin_funding_rate) / 100;
    }
    
    try {
      const result = await putTriggerScanner(payload).unwrap();
      
      if (result) {
        // Success - close the edit form
        toggleExpanded(false);
      }
    } catch (err) {
      // Handle API errors
      if (err.data?.detail) {
        setError(err.data.detail);
      } else if (err.data) {
        // Map backend validation errors to form fields
        const backendErrors = {};
        Object.entries(err.data).forEach(([key, value]) => {
          backendErrors[key] = Array.isArray(value) ? value[0] : value;
        });
        setFormErrors(prev => ({ ...prev, ...backendErrors }));
      } else {
        setError(t('Failed to update scanner'));
      }
    } finally {
      setIsSubmitting(false);
    }
  }, [formState, validateForm, putTriggerScanner, _uuid, _tradeConfigUuid, toggleExpanded, t]);
  
  return (
    <Box sx={{ maxWidth: 700, mx: 'auto' }}>
      {error && (
        <Typography color="error" variant="body2" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}
      
      <Box sx={{ mt: 1 }}>
        {/* Entry/Exit Values - Two columns */}
        <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
          <TextField
            label={t('Entry')}
            name="low"
            value={formState.low}
            onChange={handleFormChange}
            variant="outlined"
            type="number"
            size="small"
            fullWidth
            required
            error={!!formErrors.low}
            helperText={formErrors.low}
            inputProps={{ step: "0.001" }}
            disabled={isSubmitting}
          />
          
          <TextField
            label={t('Exit')}
            name="high"
            value={formState.high}
            onChange={handleFormChange}
            variant="outlined"
            type="number"
            size="small"
            fullWidth
            required
            error={!!formErrors.high}
            helperText={formErrors.high}
            inputProps={{ step: "0.001" }}
            disabled={isSubmitting}
          />
        </Stack>
        
        {/* Trade Capital */}
        <TextField
          label={t('Trade Capital')}
          name="trade_capital"
          value={formState.trade_capital}
          onChange={handleFormChange}
          variant="outlined"
          type="number"
          size="small"
          fullWidth
          required
          error={!!formErrors.trade_capital}
          helperText={formErrors.trade_capital || t('Minimum value is 10000')}
          disabled={isSubmitting}
          sx={{ mb: 2 }}
        />
        
        {/* Min Trading Volume with checkbox and field in the same row */}
        <Box sx={{ mb: 2 }}>
          <FormControlLabel
            control={
              <Checkbox
                checked={formState.enableMinTargetAtp}
                onChange={handleFormChange}
                name="enableMinTargetAtp"
                disabled={isSubmitting}
                size="small"
              />
            }
            label={t('Enable Minimum Trading Volume')}
          />
          
          <TextField
            label={t('Minimum Trading Volume')}
            name="min_target_atp"
            value={formState.min_target_atp}
            onChange={handleFormChange}
            variant="outlined"
            type="number"
            size="small"
            fullWidth
            disabled={!formState.enableMinTargetAtp || isSubmitting}
            error={!!formErrors.min_target_atp}
            helperText={formErrors.min_target_atp}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  {t('100M')}
                </InputAdornment>
              ),
            }}
          />
        </Box>
        
        {/* Min Funding Rate with checkbox and field in the same row */}
        <Box sx={{ mb: 2 }}>
          <FormControlLabel
            control={
              <Checkbox
                checked={formState.enableMinOriginFundingRate}
                onChange={handleFormChange}
                name="enableMinOriginFundingRate"
                disabled={isSubmitting}
                size="small"
              />
            }
            label={t('Enable Minimum Funding Rate')}
          />
          
          <TextField
            label={t('Minimum Funding Rate')}
            name="min_origin_funding_rate"
            value={formState.min_origin_funding_rate}
            onChange={handleFormChange}
            variant="outlined"
            type="number"
            size="small"
            fullWidth
            disabled={!formState.enableMinOriginFundingRate || isSubmitting}
            error={!!formErrors.min_origin_funding_rate}
            helperText={formErrors.min_origin_funding_rate}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  %
                </InputAdornment>
              ),
            }}
          />
        </Box>
        
        {/* Max Iteration and Interval in a row */}
        <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
          <TextField
            label={t('Maximum Iteration')}
            name="max_repeat_num"
            value={formState.max_repeat_num}
            onChange={handleFormChange}
            variant="outlined"
            type="number"
            size="small"
            fullWidth
            required
            error={!!formErrors.max_repeat_num}
            helperText={formErrors.max_repeat_num}
            disabled={isSubmitting}
            inputProps={{ min: "1" }}
          />
          
          <TextField
            label={t('Registration Interval (seconds)')}
            name="repeat_term_secs"
            value={formState.repeat_term_secs}
            onChange={handleFormChange}
            variant="outlined"
            type="number"
            size="small"
            fullWidth
            required
            error={!!formErrors.repeat_term_secs}
            helperText={formErrors.repeat_term_secs}
            disabled={parseInt(formState.max_repeat_num, 10) === 1 || isSubmitting}
            inputProps={{ min: "1" }}
          />
        </Stack>
        
        <Stack direction="row" spacing={2} justifyContent="flex-end">
          <Button 
            onClick={() => toggleExpanded(false)} 
            disabled={isSubmitting}
            size="small"
          >
            {t('Cancel')}
          </Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained" 
            disabled={isSubmitting || isUpdateLoading}
            size="small"
            startIcon={isSubmitting || isUpdateLoading ? <CircularProgress size={16} /> : null}
          >
            {t('Update')}
          </Button>
        </Stack>
      </Box>
    </Box>
  );
} 