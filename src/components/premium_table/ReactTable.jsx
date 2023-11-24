import React, { useCallback, useEffect, useMemo, useState } from 'react';

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
import Button from '@mui/material/Button';
import LinearProgress from '@mui/material/LinearProgress';
import Skeleton from '@mui/material/Skeleton';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown';
import ArrowDropUpIcon from '@mui/icons-material/ArrowDropUp';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

import useMediaQuery from '@mui/material/useMediaQuery';
import { alpha, styled, useTheme } from '@mui/material/styles';

import { useTranslation } from 'react-i18next';

import isUndefined from 'lodash/isUndefined';
import shuffle from 'lodash/shuffle';

const DEFAULT_PAGE_SIZE = 50;

function ReactTable({
  columns,
  data,
  contextData,
  renderSubComponent,
  searchKeyword,
  isLoading,
  showProgressBar,
}) {
  const { t } = useTranslation();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [columnVisibility, setColumnVisibility] = useState({});
  const [expanded, setExpanded] = useState({});
  const [globalFilter, setGlobalFilter] = React.useState('');
  const [pagination, setPagination] = React.useState({
    pageIndex: 0,
    pageSize: DEFAULT_PAGE_SIZE,
  });
  const [sorting, setSorting] = useState([]);

  const sortWithStarred = useCallback((rowA, rowB, columnId) => {
    if (
      !isUndefined(rowA.original.favoriteAssetId) &&
      isUndefined(rowB.original.favoriteAssetId)
    )
      return -1;
    if (
      !isUndefined(rowB.original.favoriteAssetId) &&
      isUndefined(rowA.original.favoriteAssetId)
    )
      return 0;
    if (rowA.original[columnId] > rowB.original[columnId]) return 1;
    if (rowA.original[columnId] < rowB.original[columnId]) return -1;
    return 0;
  }, []);

  const table = useReactTable({
    data,
    columns,

    defaultColumn: { sortingFn: sortWithStarred },
    getRowId: (row) => row.name,

    state: {
      columnVisibility,
      expanded,
      globalFilter,
      pagination,
      sorting,
    },

    onExpandedChange: (newExpanded) => setExpanded(newExpanded()),
    onGlobalFilterChange: setGlobalFilter,
    onPaginationChange: setPagination,
    onSortingChange: setSorting,
    // Pipeline
    getCoreRowModel: getCoreRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  const loadingWidths = useMemo(
    () => shuffle([...Array(10).keys()].map((item) => (item + 10) * 5)),
    []
  );

  useEffect(() => {
    setGlobalFilter(searchKeyword);
  }, [searchKeyword]);

  useEffect(() => {
    setColumnVisibility({
      chart: !isMobile,
      spread: !isMobile,
      favoriteAssetId: !isMobile,
    });
  }, [isMobile]);

  const { rows } = table.getRowModel();

  return (
    <Box sx={{ boxShadow: 2 }}>
      {showProgressBar && <LinearProgress />}
      <Table>
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <Tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <Th
                  key={header.id}
                  colSpan={header.colSpan}
                  sx={{ width: header.getSize() }}
                >
                  {header.isPlaceholder ? null : (
                    <Stack
                      alignItems="center"
                      direction="row"
                      spacing={0}
                      onClick={header.column.getToggleSortingHandler()}
                      sx={
                        header.column.getCanSort() ? { cursor: 'pointer' } : {}
                      }
                    >
                      <Box
                        component="span"
                        sx={{
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
                          whiteSpace: 'normal',
                          wordWrap: 'break-word',
                        }}
                      >
                        {flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                      </Box>
                      {{
                        asc: <ArrowDropUpIcon />,
                        desc: <ArrowDropDownIcon />,
                      }[header.column.getIsSorted()] ?? (
                        <Box sx={{ height: '1em', width: '1em' }} />
                      )}
                    </Stack>
                  )}
                </Th>
              ))}
            </Tr>
          ))}
        </thead>
        <tbody>
          {!isLoading
            ? rows.map((row) => (
                <MemoizedRow
                  key={row.id}
                  row={row}
                  contextData={{ ...contextData, isMobile }}
                  renderSubComponent={renderSubComponent}
                />
              ))
            : loadingWidths.map((item) => (
                <Tr key={item}>
                  {table.getVisibleFlatColumns().map((column, index) => (
                    <Td key={`${item}-${column.id}`}>
                      <Skeleton
                        animation="wave"
                        variant="text"
                        sx={{ mx: 1 }}
                        width={
                          index > 0 &&
                          index < table.getVisibleFlatColumns().length - 1
                            ? item
                            : 0
                        }
                      />
                    </Td>
                  ))}
                </Tr>
              ))}
        </tbody>
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
              {t('No data to display')}
            </Typography>
          )}
          {rows.length >= DEFAULT_PAGE_SIZE && (
            <Button
              color={table.getCanNextPage() ? 'primary' : 'secondary'}
              endIcon={
                table.getCanNextPage() ? <ExpandMoreIcon /> : <ExpandLessIcon />
              }
              onClick={() => {
                table.setPageSize(
                  table.getCanNextPage()
                    ? pagination.pageSize + DEFAULT_PAGE_SIZE
                    : DEFAULT_PAGE_SIZE
                );
                if (!table.getCanNextPage()) window.scrollTo(0, 0);
              }}
              sx={{
                fontSize: '0.85rem',
                fontStyle: 'italic',
                letterSpacing: '0.085em',
                textTransform: 'none',
                ':hover': { backgroundColor: 'unset' },
              }}
            >
              {table.getCanNextPage() ? t('See more') : t('See less')}
            </Button>
          )}
        </Box>
      )}
    </Box>
  );
}

const MemoizedRow = React.memo(({ row, contextData, renderSubComponent }) => {
  const theme = useTheme();
  const { t } = useTranslation();

  return (
    <>
      <Tr
        onClick={() => row.toggleExpanded(!row.getIsExpanded())}
        sx={{
          cursor: 'pointer',
          ...(row.getIsExpanded()
            ? { bgcolor: theme.palette.background.paper }
            : {}),
        }}
      >
        {row.getVisibleCells().map((cell) => (
          <Td key={cell.id}>
            {flexRender(cell.column.columnDef.cell, {
              ...cell.getContext(),
              ...contextData,
              theme,
              t,
            })}
          </Td>
        ))}
      </Tr>
      {row.getIsExpanded() && (
        <Tr key={`${row.id}-expand-panel`}>
          <Td colSpan={row.getVisibleCells().length}>
            {renderSubComponent({ row, contextData })}
          </Td>
        </Tr>
      )}
    </>
  );
});

const Table = styled('table')(() => ({
  borderCollapse: 'collapse',
  borderRadius: 5,
  fontSize: '0.88em',
  tableLayout: 'fixed',
  width: '100%',
}));
const Td = styled('td')(() => ({
  height: 50,
  textAlign: 'left',
}));
const Th = styled('th')(({ theme }) => ({
  backgroundColor: alpha(theme.palette.background.paper, 0.5),
  height: 30,
  textAlign: 'left',
}));
const Tr = styled('tr')(({ theme }) => ({
  borderBottom: `1px solid ${
    theme.palette.mode === 'dark'
      ? theme.palette.grey['900']
      : alpha(theme.palette.grey['100'], 0.5)
  }`,
}));

export default React.memo(ReactTable);
