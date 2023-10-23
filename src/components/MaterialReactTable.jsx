/* eslint-disable react/jsx-pascal-case */
/* eslint-disable camelcase */
import React, { useMemo, useRef } from 'react';

import {
  MaterialReactTable,
  MRT_FullScreenToggleButton,
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
  muiSearchTextFieldProps: {
    size: 'small',
    variant: 'outlined',
    inputProps: { style: { marginBottom: '2px' } },
    sx: { ml: { xs: -1, sm: 0 } },
  },
  muiTableProps: { sx: { tableLayout: 'fixed' } },
  muiTableBodyCellProps: { sx: { px: { xs: 0, sm: 0.5 } } },
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

  const tableTheme = useMemo(
    () =>
      createTheme({
        ...globalTheme,
        palette: {
          ...globalTheme.palette,
          background: { default: globalTheme.palette.background.paper },
        },
      }),
    [globalTheme]
  );

  const matchLargeScreen = useMediaQuery('(min-width:600px)');

  const tableProps = useMemo(() => {
    const propsObj = {};
    const muiTopToolbarProps = {};
    Object.keys(merge(DEFAULT_PROPS, props)).forEach((prop) => {
      if (props[prop]) {
        if (isObject(props[prop]))
          propsObj[prop] = merge(DEFAULT_PROPS[prop], props[prop]);
        else propsObj[prop] = props[prop];
      } else propsObj[prop] = DEFAULT_PROPS[prop];
    });
    if (!matchLargeScreen)
      muiTopToolbarProps.sx = { span: { display: 'none' } };
    propsObj.muiTopToolbarProps = muiTopToolbarProps;
    return propsObj;
  }, [matchLargeScreen, props]);

  return (
    <ThemeProvider theme={tableTheme}>
      <MaterialReactTable
        tableInstanceRef={ref}
        columns={cols}
        data={rows}
        state={state}
        localization={localization}
        positionGlobalFilter={matchLargeScreen ? 'right' : 'left'}
        renderToolbarInternalActions={({ table }) => (
          <>
            <MRT_ToggleDensePaddingButton table={table} />
            <MRT_FullScreenToggleButton table={table} />
          </>
        )}
        {...tableProps}
        renderDetailPanel={renderDetailPanel}
        renderTopToolbarCustomActions={renderTopToolbarCustomActions}
        muiTableHeadCellProps={({ column }) => ({
          sx: {
            color: column.getIsSorted()
              ? globalTheme.palette.text.main
              : globalTheme.palette.grey[
                  globalTheme.palette.mode === 'dark' ? '100' : '700'
                ],
            fontSize: '0.725em',
            ...(props.muiTableHeadCellProps?.sx || {}),
          },
          ...(props.muiTableHeadCellProps || {}),
        })}
      />
    </ThemeProvider>
  );
}
