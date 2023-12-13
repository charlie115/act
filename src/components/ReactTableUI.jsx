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
import Stack from '@mui/material/Stack';
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
      extraData,
      options,
      renderSubComponent,
      getCellProps,
      getRowProps,
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

    if (ref) ref.current = table;

    return (
      <Box>
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
                          header.column.getCanSort()
                            ? {
                                cursor: 'pointer',
                                ...header.column.columnDef.props?.sx,
                              }
                            : { ...header.column.columnDef.props?.sx }
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
              ? rows.map((row) =>
                  renderRow ? (
                    renderRow({
                      row,
                      extraData,
                      renderSubComponent,
                      getCellProps,
                      getRowProps,
                      theme,
                      isMobile,
                    })
                  ) : (
                    <MemoizedRow
                      key={row.id}
                      row={row}
                      extraData={extraData}
                      renderSubComponent={renderSubComponent}
                      getCellProps={getCellProps}
                      getRowProps={getRowProps}
                      theme={theme}
                      isMobile={isMobile}
                    />
                  )
                )
              : [...Array(10).keys()].map((item) => (
                  <Tr key={item}>
                    {table.getVisibleFlatColumns().map((column, index) => (
                      <Td
                        key={`${item}-${column.id}`}
                        align="center"
                        height={40}
                        {...(getCellProps ? getCellProps() : {})}
                      >
                        <Skeleton
                          animation="wave"
                          variant="text"
                          sx={{ mx: 2 }}
                          width={column.getSize() * 0.9}
                          // width={(column.getSize() - index) / 2}
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
          </Box>
        )}
      </Box>
    );
  }
);

const MemoizedRow = React.memo(
  ({
    row,
    extraData,
    renderSubComponent,
    getCellProps,
    getRowProps,
    theme,
    isMobile,
  }) => (
    <>
      <Tr {...(getRowProps ? getRowProps(row) : {})}>
        {row
          .getVisibleCells()
          .filter((cell) => cell.getValue() !== false)
          .map((cell) => (
            <Td
              key={cell.id}
              {...(getCellProps ? getCellProps(cell) : {})}
              {...cell.column.columnDef.props}
            >
              {flexRender(cell.column.columnDef.cell, {
                ...cell.getContext(),
                ...extraData,
                isMobile,
                theme,
              })}
            </Td>
          ))}
      </Tr>
      {row.getIsExpanded() && renderSubComponent && (
        <Tr key={`${row.id}-expand-panel`}>
          <Td colSpan={row.getVisibleCells().length}>
            {renderSubComponent({ row, extraData })}
          </Td>
        </Tr>
      )}
    </>
  )
);

export const Table = styled('table')(() => ({
  borderCollapse: 'collapse',
  borderRadius: 5,
  fontSize: '0.88em',
  tableLayout: 'fixed',
  width: '100%',
}));
export const Td = styled('td')(() => ({
  // height: 50,
  textAlign: 'left',
}));
export const Th = styled('th')(({ theme }) => ({
  backgroundColor: alpha(theme.palette.background.paper, 0.5),
  height: 30,
  textAlign: 'left',
}));
export const Tr = styled('tr')(({ theme }) => ({
  borderBottom: `1px solid ${
    theme.palette.mode === 'dark'
      ? theme.palette.grey['900']
      : alpha(theme.palette.grey['100'], 0.5)
  }`,
}));

export default React.memo(ReactTableUI);
