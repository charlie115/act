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
import Typography from '@mui/material/Typography';

import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown';
import ArrowDropUpIcon from '@mui/icons-material/ArrowDropUp';

import useMediaQuery from '@mui/material/useMediaQuery';
import { alpha, styled, useTheme } from '@mui/material/styles';

import { useTranslation } from 'react-i18next';

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
      <Box>
        {showProgressBar && <LinearProgress />}
        <Table {...(getTableProps ? getTableProps(table) : {})}>
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead
                    key={header.id}
                    colSpan={header.colSpan}
                    onClick={header.column.getToggleSortingHandler()}
                    sx={{
                      width: header.getSize(),
                      color: header.column.getIsSorted()
                        ? theme.palette.text.main
                        : theme.palette.grey[
                            theme.palette.mode === 'dark' ? '200' : '700'
                          ],
                      fontSize: {
                        xs: '0.5rem',
                        md: '0.6rem',
                        lg: '0.7rem',
                      },
                      lineHeight: 1.1,
                      userSelect: 'none',
                      verticalAlign: 'middle',
                      whiteSpace: 'normal',
                      wordWrap: 'break-word',
                      ...(getHeaderProps ? getHeaderProps(header)?.sx : {}),
                      ...header.column.columnDef.props?.sx,
                      ...header.column.columnDef.slotProps?.header?.sx,
                      cursor: header.column.getCanSort()
                        ? 'pointer'
                        : undefined,
                      ...(header.isPlaceholder ? { opacity: 0 } : {}),
                      ...(hideHeader ? { height: 0 } : {}),
                    }}
                  >
                    {hideHeader || header.isPlaceholder ? null : (
                      <Box component="span" sx={{ position: 'relative' }}>
                        {flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                        {{
                          asc: (
                            <ArrowDropUpIcon
                              sx={{
                                color: 'text.main',
                                position: 'absolute',
                                bottom: '50%',
                                right: '-1em',
                                transform: 'translateY(50%)',
                              }}
                            />
                          ),
                          desc: (
                            <ArrowDropDownIcon
                              sx={{
                                color: 'text.main',
                                position: 'absolute',
                                bottom: '50%',
                                right: '-1em',
                                transform: 'translateY(50%)',
                              }}
                            />
                          ),
                        }[header.column.getIsSorted()] ?? null}
                      </Box>
                    )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </thead>

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
                          height={40}
                        >
                          <Skeleton
                            animation="wave"
                            variant="text"
                            sx={{ width: column.getSize() < 2 ? 0 : '90%' }}
                            height={isMobile ? 10 : 15}
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
                    // 5,
                    // 10,
                    // 25,
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
                    '& .MuiTablePagination-toolbar': { minHeight: 0 },
                  }}
                />
              </TableRow>
            </tfoot>
          )}
        </Table>
        {!isLoading && (
          <Box sx={{ textAlign: 'center' }}>
            {rows.length === 0 && (
              <Typography
                sx={{
                  color: 'secondary.main',
                  fontSize: '0.85rem',
                  fontStyle: 'italic',
                  py: 5,
                }}
              >
                {noDisplayMessage || t('No data to display')}
              </Typography>
            )}
          </Box>
        )}
      </Box>
    );
  }
);

const MemoizedRow = React.memo(
  ({ row, table, renderSubComponent, getCellProps, getRowProps }) => (
    <>
      <TableRow {...(getRowProps ? getRowProps(row, { table }) : {})}>
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
          <TableCell colSpan={row.getVisibleCells().length} sx={{ p: 0 }}>
            {renderSubComponent({ row, meta: table.options.meta })}
          </TableCell>
        </TableRow>
      )}
    </>
  )
);

export const Table = styled('table')(() => ({
  borderCollapse: 'collapse',
  fontSize: '0.88em',
  paddingLeft: '4px',
  paddingRight: '4px',
  tableLayout: 'fixed',
  width: '100%',
}));
export const TableCell = styled('td')(({ theme }) => ({
  // height: 50,
  overflowWrap: 'break-word',
  textAlign: 'left',
  paddingLeft: '4px',
  paddingRight: '4px',
  [theme.breakpoints.down('md')]: { fontSize: '0.75em' },
}));
export const TableHead = styled('th')(({ theme }) => ({
  backgroundColor: alpha(theme.palette.background.paper, 0.5),
  height: 30,
  textAlign: 'left',
}));
export const TableRow = styled('tr')(({ theme }) => ({
  borderBottom: `1px solid ${
    theme.palette.mode === 'dark'
      ? theme.palette.grey['900']
      : alpha(theme.palette.grey['100'], 0.5)
  }`,
}));

export default React.memo(ReactTableUI);
