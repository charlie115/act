import React, { forwardRef, useCallback } from 'react';

import {
  flexRender,
  getCoreRowModel,
  getExpandedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table';

import Box from '@mui/material/Box';
import LinearProgress from '@mui/material/LinearProgress';
import Skeleton from '@mui/material/Skeleton';
import TablePagination from '@mui/material/TablePagination';
import Paper from '@mui/material/Paper';

import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown';
import ArrowDropUpIcon from '@mui/icons-material/ArrowDropUp';

import useMediaQuery from '@mui/material/useMediaQuery';
import { styled, useTheme } from '@mui/material/styles';

import { useTranslation } from 'react-i18next';

import alpha from '../configs/theme/safeAlpha';
import EmptyState from './EmptyState';

const ReactTableUI = forwardRef(
  (
    {
      columns,
      data,
      options,
      enableTablePaginationUI,
      renderSubComponent,
      getHeaderProps,
      getCellProps,
      getRowProps,
      getTableProps,
      hideHeader,
      noDisplayMessage,
      showProgressBar,
      isLoading,
      renderRow,
    },
    ref
  ) => {
    const { t } = useTranslation();

    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('md'));

    const getSubRows = useCallback((row) => row.subRows, []);

    const table = useReactTable({
      data,
      columns,
      ...options,
      getCoreRowModel: getCoreRowModel(),
      getExpandedRowModel: getExpandedRowModel(),
      getFilteredRowModel: getFilteredRowModel(),
      getPaginationRowModel: getPaginationRowModel(),
      getSortedRowModel: getSortedRowModel(),
      getSubRows,
    });

    const { rows } = table.getRowModel();

    const { pageSize, pageIndex } = table.getState().pagination;

    if (ref) ref.current = table;

    return (
      <TableContainer elevation={0}>
        {showProgressBar && (
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
        <Table {...(getTableProps ? getTableProps(table) : {})}>
          {!hideHeader && (
            <TableHead component="thead">
              {table.getHeaderGroups().map((headerGroup) => (
                <TableRow key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <TableHeaderCell
                      key={header.id}
                      colSpan={header.colSpan}
                      onClick={header.column.getToggleSortingHandler()}
                      $canSort={header.column.getCanSort()}
                      $isSorted={header.column.getIsSorted()}
                      sx={{
                        width: header.getSize(),
                        ...(getHeaderProps ? getHeaderProps(header)?.sx : {}),
                        ...header.column.columnDef.props?.sx,
                        ...header.column.columnDef.slotProps?.header?.sx,
                        ...(header.isPlaceholder ? { opacity: 0 } : {}),
                      }}
                    >
                      {!header.isPlaceholder && (
                        <HeaderContent>
                          {flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                          {header.column.getIsSorted() && (
                            <SortIcon>
                              {header.column.getIsSorted() === 'asc' ? (
                                <ArrowDropUpIcon fontSize="small" />
                              ) : (
                                <ArrowDropDownIcon fontSize="small" />
                              )}
                            </SortIcon>
                          )}
                        </HeaderContent>
                      )}
                    </TableHeaderCell>
                  ))}
                </TableRow>
              ))}
            </TableHead>
          )}

          <tbody>
            {!isLoading
              ? rows.map((row) =>
                  renderRow ? (
                    renderRow({
                      row,
                      table,
                      renderSubComponent,
                      getCellProps,
                      getRowProps,
                    })
                  ) : (
                    <MemoizedRow
                      key={row.id}
                      row={row}
                      table={table}
                      renderSubComponent={renderSubComponent}
                      getCellProps={getCellProps}
                      getRowProps={getRowProps}
                    />
                  )
                )
              : [...Array(pageSize || 10).keys()].map((item) => (
                  <TableRow key={item}>
                    {table
                      .getVisibleFlatColumns()
                      .filter((column) => column.columns.length === 0)
                      .map((column) => (
                        <TableCell
                          key={`${item}-${column.id}`}
                          align="center"
                          {...(getCellProps ? getCellProps() : {})}
                          height={48}
                        >
                          <Skeleton
                            animation="wave"
                            variant="text"
                            sx={{ width: column.getSize() < 2 ? 0 : '90%' }}
                            height={isMobile ? 12 : 16}
                          />
                        </TableCell>
                      ))}
                  </TableRow>
                ))}
          </tbody>
          {enableTablePaginationUI && data.length > 0 && !isLoading && (
            <tfoot>
              <TableRow>
                <TablePagination
                  count={table.getFilteredRowModel().rows.length}
                  rowsPerPageOptions={[
                    { label: t('All'), value: data.length },
                  ]}
                  colSpan={columns.length}
                  rowsPerPage={pageSize}
                  page={pageIndex}
                  shape="rounded"
                  size="small"
                  labelRowsPerPage={t('Rows')}
                  onPageChange={(_, page) => {
                    table.setPageIndex(page);
                  }}
                  onRowsPerPageChange={(e) => {
                    const size = e.target.value ? Number(e.target.value) : 10;
                    table.setPageSize(size);
                  }}
                  sx={{
                    borderBottom: 0,
                    '& .MuiTablePagination-toolbar': { 
                      minHeight: 48,
                      paddingLeft: 2,
                      paddingRight: 2,
                    },
                  }}
                />
              </TableRow>
            </tfoot>
          )}
        </Table>
        {!isLoading && rows.length === 0 && (
          <EmptyState
            variant="no-data"
            title={noDisplayMessage || t('No data to display')}
            description={t('There are no items to show at the moment.')}
            compact
          />
        )}
      </TableContainer>
    );
  }
);

const MemoizedRow = React.memo(
  ({ row, table, renderSubComponent, getCellProps, getRowProps }) => (
    <>
      <TableRow 
        $isExpanded={row.getIsExpanded()}
        {...(getRowProps ? getRowProps(row, { table }) : {})}
      >
        {row.getVisibleCells().map((cell) => (
          <TableCell
            key={cell.id}
            {...(getCellProps ? getCellProps(cell, { table }) : {})}
            {...cell.column.columnDef.props}
            {...cell.column.columnDef.slotProps?.cell}
          >
            {flexRender(cell.column.columnDef.cell, {
              ...cell.getContext(),
            })}
          </TableCell>
        ))}
      </TableRow>
      {row.getIsExpanded() && renderSubComponent && (
        <TableRow key={`${row.id}-expand-panel`}>
          <TableCell 
            colSpan={row.getVisibleCells().length} 
            sx={{ 
              p: 0,
              backgroundColor: (theme) => alpha(theme.palette.primary?.main || '#007cff', 0.02),
            }}
          >
            {renderSubComponent({ row, meta: table.options.meta })}
          </TableCell>
        </TableRow>
      )}
    </>
  )
);

// Modern table container
const TableContainer = styled(Paper)(({ theme }) => ({
  borderRadius: '6px !important',
  overflow: 'hidden',
  border: `1px solid ${theme.palette.divider}`,
  position: 'relative',
  backgroundColor: theme.palette.background.paper,
  transition: theme.transitions.create(['box-shadow'], {
    duration: theme.transitions.duration.short,
  }),
  '&:hover': {
    boxShadow: theme.shadows[2],
  },
}));

// Enhanced table styling
export const Table = styled('table')(({ theme }) => ({
  borderCollapse: 'collapse',
  fontSize: theme.typography.fontSize,
  tableLayout: 'fixed',
  width: '100%',
}));

// Modern table cell
export const TableCell = styled('td')(({ theme }) => ({
  padding: theme.spacing(1, 1.5),
  overflowWrap: 'break-word',
  textAlign: 'left',
  fontSize: theme.typography.body2.fontSize,
  borderBottom: `1px solid ${alpha(theme.palette.divider || '#E0E0E0', 0.5)}`,
  [theme.breakpoints.down('md')]: {
    padding: theme.spacing(0.75, 0.5),
    fontSize: '0.75rem',
    lineHeight: 1.3,
  },
}));

// Enhanced table header
export const TableHead = styled('thead')(({ theme }) => ({
  borderBottom: `2px solid ${theme.palette.divider}`,
}));

// Modern table header cell
export const TableHeaderCell = styled('th', {
  shouldForwardProp: (prop) => !['$canSort', '$isSorted'].includes(prop),
})(({ theme, $canSort, $isSorted }) => ({
    backgroundColor: theme.palette.mode === 'dark' 
      ? theme.palette.background.paper 
      : theme.palette.grey[50],
    padding: theme.spacing(1.5, 1.5),
    textAlign: 'center',
    fontWeight: theme.typography.fontWeightBold,
    fontSize: theme.typography.body2.fontSize,
    color: $isSorted ? theme.palette.primary.main : theme.palette.text.primary,
    userSelect: 'none',
    position: 'relative',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    cursor: $canSort ? 'pointer' : 'default',
    transition: theme.transitions.create(['background-color', 'color'], {
      duration: theme.transitions.duration.short,
    }),
    '&:hover': $canSort ? {
      backgroundColor: alpha(theme.palette.primary?.main || '#007cff', 0.04),
    } : {},
    [theme.breakpoints.down('md')]: {
      padding: theme.spacing(0.5, 0.375),
      fontSize: '0.625rem',
      textAlign: 'center',
      whiteSpace: 'normal',
      lineHeight: 1.2,
      wordBreak: 'break-word',
    },
  })
);

// Header content wrapper
const HeaderContent = styled(Box)({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  gap: 4,
});

// Sort icon wrapper
const SortIcon = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  color: theme.palette.primary.main,
  marginLeft: 4,
}));

// Enhanced table row
export const TableRow = styled('tr', {
  shouldForwardProp: (prop) => prop !== '$isExpanded',
})(({ theme, $isExpanded }) => ({
  borderBottom: `1px solid ${alpha(theme.palette.divider || '#E0E0E0', 0.5)}`,
  backgroundColor: $isExpanded ? alpha(theme.palette.primary?.main || '#007cff', 0.02) : 'transparent',
  transition: theme.transitions.create(['background-color'], {
    duration: theme.transitions.duration.shortest,
  }),
  '&:hover': {
    backgroundColor: alpha(theme.palette.primary?.main || '#007cff', 0.04),
  },
  '&:last-child': {
    borderBottom: 'none',
  },
}));

export default React.memo(ReactTableUI);