/* eslint-disable react/jsx-pascal-case */
/* eslint-disable camelcase */
import React, { useMemo, useRef } from 'react';

import {
  MaterialReactTable,
  MRT_FullScreenToggleButton,
  MRT_ShowHideColumnsButton,
  MRT_ToggleDensePaddingButton,
} from 'material-react-table';
import { ThemeProvider, createTheme, useTheme, alpha } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import LinearProgress from '@mui/material/LinearProgress';
import useMediaQuery from '@mui/material/useMediaQuery';

import { useTranslation } from 'react-i18next';

import isObject from 'lodash/isObject';
import merge from 'lodash/merge';

import getLocalization from 'constants/mrt_localization';

const DEFAULT_PROPS = {
  enableColumnActions: false,
  enableColumnFilters: false,
  enableColumnOrdering: false,
  enableColumnResizing: false,
  enableExpanding: true,
  enableGlobalFilter: true,
  enablePagination: false,
  enableStickyHeader: true,
  initialState: { showGlobalFilter: true },
  muiTableProps: { sx: { tableLayout: 'fixed' } },
  muiTableBodyCellProps: { sx: { px: { xs: 0.5, sm: 1 } } },
  muiTopToolbarProps: {
    sx: {
      borderBottom: 1,
      borderColor: 'divider',
      bgcolor: 'background.paper',
      '& .MuiBox-root': {
        alignItems: 'flex-end',
        mb: { xs: 0.5, md: 0.25 },
        px: { xs: 1, sm: 2 },
      },
    },
  },
  positionExpandColumn: 'last',
};

// Modern table container with enhanced styling
function TableContainer({ children, loading }) {
  const theme = useTheme();
  
  return (
    <Paper
      elevation={0}
      sx={{
        borderRadius: 2,
        overflow: 'hidden',
        border: `1px solid ${theme.palette.divider}`,
        position: 'relative',
        background: theme.palette.background.paper,
        transition: theme.transitions.create(['box-shadow'], {
          duration: theme.transitions.duration.short,
        }),
        '&:hover': {
          boxShadow: theme.shadows[2],
        },
      }}
    >
      {loading && (
        <LinearProgress 
          sx={{ 
            position: 'absolute', 
            top: 0, 
            left: 0, 
            right: 0, 
            zIndex: 1,
          }} 
        />
      )}
      {children}
    </Paper>
  );
}

export default function EnhancedMaterialReactTable({
  columns,
  data,
  state,
  renderDetailPanel,
  renderTopToolbarCustomActions,
  loading = false,
  ...props
}) {
  const ref = useRef();

  const { i18n } = useTranslation();
  const globalTheme = useTheme();

  const cols = useMemo(() => columns, [columns]);

  const localization = useMemo(() => getLocalization(), [i18n.language]);

  const isMobile = useMediaQuery(globalTheme.breakpoints.down('md'));
  const isSmallScreen = useMediaQuery('(max-width:420px)');

  // Enhanced theme for tables
  const tableTheme = useMemo(
    () =>
      createTheme({
        ...globalTheme,
        palette: {
          ...globalTheme.palette,
          background: {
            default: globalTheme.palette.background.paper,
            paper: globalTheme.palette.background.default,
          },
        },
        typography: { 
          fontSize: isMobile ? 11 : 14,
          fontFamily: globalTheme.typography.fontFamily,
        },
        components: {
          ...globalTheme.components,
          MuiTableCell: {
            styleOverrides: {
              root: {
                borderColor: globalTheme.palette.divider,
              },
            },
          },
        },
      }),
    [globalTheme, isMobile]
  );

  const tableProps = useMemo(() => {
    const propsObj = {};
    Object.keys(merge(DEFAULT_PROPS, props)).forEach((prop) => {
      if (props[prop]) {
        if (isObject(props[prop]))
          propsObj[prop] = merge(DEFAULT_PROPS[prop], props[prop]);
        else propsObj[prop] = props[prop];
      } else propsObj[prop] = DEFAULT_PROPS[prop];
    });
    return propsObj;
  }, [isSmallScreen, props]);

  return (
    <TableContainer loading={loading}>
      <ThemeProvider theme={tableTheme}>
        <MaterialReactTable
          tableInstanceRef={ref}
          columns={cols}
          data={data}
          state={state}
          localization={localization}
          positionGlobalFilter="right"
          renderToolbarInternalActions={({ table }) => (
            <Box sx={{ display: 'flex', gap: 1 }}>
              <MRT_ShowHideColumnsButton table={table} />
              <MRT_ToggleDensePaddingButton table={table} />
              <MRT_FullScreenToggleButton table={table} />
            </Box>
          )}
          {...tableProps}
          renderDetailPanel={renderDetailPanel}
          renderTopToolbarCustomActions={renderTopToolbarCustomActions}
          
          // Enhanced search field styling
          muiSearchTextFieldProps={{
            size: 'small',
            variant: 'outlined',
            placeholder: 'Search...',
            inputProps: {
              style: {
                height: isMobile ? '1.5em' : '2em',
                fontSize: isMobile ? '0.875rem' : '1rem',
              },
              ...(props.muiSearchTextFieldProps?.inputProps || {}),
            },
            sx: [
              {
                ml: { xs: 1, sm: 0 },
                '& .MuiInputBase-root': { 
                  px: { xs: 1, sm: 1.5 },
                  borderRadius: 1.5,
                  backgroundColor: alpha(globalTheme.palette.grey[500], 0.08),
                  '&:hover': {
                    backgroundColor: alpha(globalTheme.palette.grey[500], 0.12),
                  },
                  '&.Mui-focused': {
                    backgroundColor: alpha(globalTheme.palette.grey[500], 0.12),
                  },
                },
              },
              isMobile && {
                '& .MuiSvgIcon-root': { fontSize: '1.25em' },
              },
            ],
          }}
          
          // Enhanced table styling
          muiTableProps={{
            sx: {
              tableLayout: 'fixed',
              '& .MuiTableBody-root': {
                '& .MuiTableRow-root': {
                  '&:hover': {
                    backgroundColor: alpha(globalTheme.palette.primary.main, 0.04),
                  },
                },
              },
            },
            ...(props.muiTableProps || {}),
          }}
          
          // Enhanced header cell styling
          muiTableHeadCellProps={({ column }) => ({
            sx: {
              backgroundColor: globalTheme.palette.mode === 'dark' 
                ? globalTheme.palette.background.paper 
                : globalTheme.palette.grey[50],
              color: column.getIsSorted()
                ? globalTheme.palette.primary.main
                : globalTheme.palette.text.primary,
              fontWeight: 600,
              px: { xs: 1, sm: 2 },
              py: { xs: 1.5, sm: 2 },
              borderBottom: `2px solid ${globalTheme.palette.divider}`,
              '.MuiSvgIcon-root': { 
                height: '1em', 
                width: '1em',
                color: column.getIsSorted() 
                  ? globalTheme.palette.primary.main 
                  : globalTheme.palette.text.secondary,
              },
              '.Mui-TableHeadCell-Content-Wrapper': {
                fontSize: { xs: '0.75rem', sm: '0.875rem', lg: '0.875rem' },
                lineHeight: 1.2,
                whiteSpace: 'normal',
                wordWrap: 'break-word',
              },
              '&:hover': column.getCanSort() ? {
                backgroundColor: alpha(globalTheme.palette.primary.main, 0.04),
              } : {},
            },
            ...(props.muiTableHeadCellProps || {}),
          })}
          
          // Enhanced body cell styling
          muiTableBodyCellProps={{
            sx: {
              fontSize: { xs: '0.75rem', sm: '0.875rem' },
              py: { xs: 1, sm: 1.5 },
              px: { xs: 1, sm: 2 },
              borderBottom: `1px solid ${alpha(globalTheme.palette.divider, 0.5)}`,
            },
            ...(props.muiTableBodyCellProps || {}),
          }}
          
          // Enhanced row styling
          muiTableBodyRowProps={({ row }) => ({
            sx: {
              cursor: 'pointer',
              transition: globalTheme.transitions.create(['background-color'], {
                duration: globalTheme.transitions.duration.shortest,
              }),
            },
            ...(props.muiTableBodyRowProps?.(row) || {}),
          })}
        />
      </ThemeProvider>
    </TableContainer>
  );
}