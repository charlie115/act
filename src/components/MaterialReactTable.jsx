/* eslint-disable react/jsx-pascal-case */
/* eslint-disable camelcase */
import React, { useMemo, useRef } from 'react';

import {
  MaterialReactTable,
  MRT_FullScreenToggleButton,
  MRT_ShowHideColumnsButton,
  MRT_ToggleDensePaddingButton,
} from 'material-react-table';
import { ThemeProvider, createTheme, useTheme } from '@mui/material/styles';
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
  enableStickyHeader: false,
  initialState: { showGlobalFilter: true },
  muiTableProps: { sx: { tableLayout: 'fixed' } },
  muiTableBodyCellProps: { sx: { px: { xs: 0, sm: 0.5 } } },
  muiTopToolbarProps: {
    sx: {
      '& .MuiBox-root': {
        alignItems: 'flex-end',
        mb: { xs: 0.5, md: 0.25 },
        px: { xs: 0, sm: 0.5 },
      },
    },
  },
  positionExpandColumn: 'last',
};

export default function MRTable({
  columns,
  data,
  state,
  renderDetailPanel,
  renderTopToolbarCustomActions,
  ...props
}) {
  const ref = useRef();

  const { i18n } = useTranslation();
  const globalTheme = useTheme();

  const cols = useMemo(() => columns, [columns]);
  const rows = useMemo(() => data, [data]);

  const localization = useMemo(() => getLocalization(), [i18n.language]);

  const isMobile = useMediaQuery(globalTheme.breakpoints.down('md'));
  const isSmallScreen = useMediaQuery('(max-width:420px)');

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
        typography: { fontSize: isMobile ? 9.5 : 12 },
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
    <ThemeProvider theme={tableTheme}>
      <MaterialReactTable
        tableInstanceRef={ref}
        columns={cols}
        data={rows}
        state={state}
        localization={localization}
        // positionToolbarDropZone="none"
        positionGlobalFilter="right"
        renderToolbarInternalActions={({ table }) => (
          <>
            <MRT_ShowHideColumnsButton table={table} />
            <MRT_ToggleDensePaddingButton table={table} />
            <MRT_FullScreenToggleButton table={table} />
          </>
        )}
        {...tableProps}
        renderDetailPanel={renderDetailPanel}
        renderTopToolbarCustomActions={renderTopToolbarCustomActions}
        muiSearchTextFieldProps={{
          size: 'small',
          variant: 'outlined',
          inputProps: {
            style: !isSmallScreen
              ? { marginBottom: '2px', height: isMobile ? '0.75em' : undefined }
              : { fontSize: '0.75em', height: '0.5em' },
            ...(props.muiSearchTextFieldProps?.inputProps || {}),
          },
          sx: [
            {
              ml: { xs: 1, sm: 0 },
              '& .MuiInputBase-root': { px: { xs: 0.5, sm: 1 } },
            },
            isMobile && {
              '& .MuiSvgIcon-root': { fontSize: '1em' },
            },
          ],
        }}
        muiTableHeadCellProps={({ column }) => ({
          sx: {
            color: column.getIsSorted()
              ? globalTheme.palette.text.main
              : globalTheme.palette.grey[
                  globalTheme.palette.mode === 'dark' ? '100' : '700'
                ],
            px: { xs: 0.3 },
            '.MuiSvgIcon-root': { height: '0.75em', width: '0.75em' },
            '.Mui-TableHeadCell-Content-Wrapper': {
              fontSize: { xs: '0.5rem', sm: '0.65rem', lg: '0.75rem' },
              lineHeight: 1.1,
              whiteSpace: 'normal',
              wordWrap: 'break-word',
            },
          },
          ...(props.muiTableHeadCellProps || {}),
        })}
      />
    </ThemeProvider>
  );
}
