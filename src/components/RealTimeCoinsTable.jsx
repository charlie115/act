import React, { useCallback, useEffect, useMemo, useState } from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Collapse from '@mui/material/Collapse';
import Grid from '@mui/material/Grid';
import LinearProgress from '@mui/material/LinearProgress';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

import BlockIcon from '@mui/icons-material/Block';
import InsightsIcon from '@mui/icons-material/Insights';
import StarIcon from '@mui/icons-material/Star';
import StarOutlineIcon from '@mui/icons-material/StarOutline';

import { alpha, useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

import { useTranslation } from 'react-i18next';

import { useDispatch, useSelector } from 'react-redux';
import {
  addLocalFavoriteSymbol,
  removeLocalFavoriteSymbol,
} from 'redux/reducers/home';
import {
  useCreateUsersFavoriteSymbolsMutation,
  useDeleteUsersFavoriteSymbolsMutation,
  useGetUsersFavoriteSymbolsQuery,
} from 'redux/api/drf';
import { useGetWsCoinsQuery } from 'redux/api/websocket';

import debounce from 'lodash/debounce';
import isNumber from 'lodash/isNumber';
import isUndefined from 'lodash/isUndefined';
import orderBy from 'lodash/orderBy';

import formatIntlNumber from 'utils/formatIntlNumber';
import formatShortNumber from 'utils/formatShortNumber';

import LightWeightKLineChart from 'components/charts/LightWeightKLineChart';
import MarketExchangeSelector from 'components/MarketExchangeSelector';
import MaterialReactTable from 'components/MaterialReactTable';

import { coinicons } from 'assets/exports';

const REALTIME_INTERVAL_KEY = '1T';

const HISTORICAL_DATA = [];

export default function RealTimeCoinsTable() {
  const dispatch = useDispatch();

  const { i18n, t } = useTranslation();

  const theme = useTheme();

  const { loggedin } = useSelector((state) => state.auth);

  const [expanded, setExpanded] = useState({});

  const [selectedExchanges, setSelectedExchanges] = useState(null);
  // const { data } = useGetWsCoinsQuery(
  //   { ...selectedExchanges, period: selectedInterval },
  //   { skip: !selectedExchanges || selectedInterval === REALTIME_INTERVAL_KEY }
  // );

  const localFavoriteSymbols = useSelector(
    (state) =>
      state.home.favoriteSymbols[
        `${selectedExchanges?.baseExchange}:${selectedExchanges?.compareExchange}`
      ]
  );
  const { assets } = useSelector((state) => state.websocket);

  const { data: realTimeData, isLoading } = useGetWsCoinsQuery(
    { ...selectedExchanges, period: REALTIME_INTERVAL_KEY },
    { skip: !selectedExchanges }
  );

  const { data: favoriteSymbols } = useGetUsersFavoriteSymbolsQuery(
    {
      market_name_1: selectedExchanges?.baseExchange,
      market_name_2: selectedExchanges?.compareExchange,
    },
    { skip: !(loggedin && selectedExchanges) }
  );

  const [createFavoriteSymbol, createFavoriteRes] =
    useCreateUsersFavoriteSymbolsMutation();
  const [deleteFavoriteSymbol, deleteFavoriteRes] =
    useDeleteUsersFavoriteSymbolsMutation();

  const matchLargeScreen = useMediaQuery('(min-width:600px)');

  const handleAddFavoriteSymbol = useCallback(
    (symbol) => {
      const marketExchangeKey = `${selectedExchanges?.baseExchange}:${selectedExchanges?.compareExchange}`;
      if (loggedin)
        createFavoriteSymbol({
          base_symbol: symbol,
          market_name_1: selectedExchanges?.baseExchange,
          market_name_2: selectedExchanges?.compareExchange,
        });
      else dispatch(addLocalFavoriteSymbol({ marketExchangeKey, symbol }));
    },
    [loggedin, selectedExchanges]
  );
  const handleRemoveFavoriteSymbol = useCallback(
    (id) => {
      const marketExchangeKey = `${selectedExchanges?.baseExchange}:${selectedExchanges?.compareExchange}`;
      if (loggedin) deleteFavoriteSymbol(id);
      else dispatch(removeLocalFavoriteSymbol({ marketExchangeKey, id }));
    },
    [loggedin, selectedExchanges]
  );

  const handleExpandRow = (newExpanded) => setExpanded(newExpanded);
  const debouncedHandleExpandRow = useCallback(
    debounce(handleExpandRow, 100, {
      leading: true,
      trailing: true,
    }),
    []
  );

  const renderNameCell = ({ renderedCellValue, row }) => (
    <Stack
      direction="row"
      spacing={1}
      sx={{ alignItems: 'center' }}
      onClick={() =>
        debouncedHandleExpandRow({ [row.id]: !row.getIsExpanded() })
      }
    >
      {row.original.icon ? (
        <img loading="lazy" width="15" src={row.original.icon} alt="" />
      ) : (
        <BlockIcon color="secondary" sx={{ fontSize: 15 }} />
      )}
      <Box component="span" sx={{ fontSize: 16 }}>
        {renderedCellValue}
      </Box>
    </Stack>
  );

  const renderNameHeader = ({ column }) => (
    <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
      <Box sx={{ width: '15px' }} />
      {column.columnDef.header}
    </Stack>
  );

  const renderExpandCell = ({ row }) => (
    <InsightsIcon
      onClick={() =>
        debouncedHandleExpandRow({
          [row.id]: !row.getIsExpanded(),
        })
      }
      color={row.getIsExpanded() ? 'info' : ''}
      fontSize="small"
    />
  );

  const renderStarCell = ({ cell, row }) =>
    !isUndefined(cell.getValue()) ? (
      <StarIcon
        fontSize="small"
        color="accent"
        onClick={() => handleRemoveFavoriteSymbol(cell.getValue())}
      />
    ) : (
      <StarOutlineIcon
        fontSize="small"
        onClick={() => handleAddFavoriteSymbol(row.original.name)}
      />
    );

  const renderPriceCell = ({ cell, row: { original } }) => (
    <>
      {formatIntlNumber(cell.getValue(), cell.getValue() > 0 ? 0 : 4)}
      <Box
        component="small"
        sx={{
          color: original.scr > 0 ? 'success.main' : 'error.main',
          display: 'inline',
          fontSize: 12,
          fontWeight: 700,
          ml: 1,
        }}
      >
        {original.scr > 0 ? '+' : ''}
        {original.scr?.toFixed(2)}%
      </Box>
      <Typography sx={{ color: 'secondary.main' }}>
        {formatIntlNumber(
          original.converted_tp,
          original.converted_tp > 0 ? 0 : 4
        )}
      </Typography>
    </>
  );

  const renderPremiumCell = ({ cell }) => (
    <>
      <Typography sx={{ display: 'inline', fontSize: 17, fontWeight: 700 }}>
        {formatIntlNumber(cell.getValue(), 3)}
      </Typography>{' '}
      <small>%</small>
    </>
  );

  const sortWithStarred = useCallback((rowA, rowB, columnId) => {
    if (
      !isUndefined(rowA.original.favoriteSymbolId) &&
      isUndefined(rowB.original.favoriteSymbolId)
    )
      return -1;
    if (
      !isUndefined(rowB.original.favoriteSymbolId) &&
      isUndefined(rowA.original.favoriteSymbolId)
    )
      return 0;
    if (rowA.original[columnId] > rowB.original[columnId]) return 1;
    if (rowA.original[columnId] < rowB.original[columnId]) return -1;
    return 0;
  }, []);

  const tableData = useMemo(
    () =>
      orderBy(
        assets?.map((asset) => {
          let favoriteSymbolId;
          if (loggedin) favoriteSymbolId = favoriteSymbols?.[asset];
          else {
            const index = localFavoriteSymbols?.indexOf(asset);
            favoriteSymbolId = index < 0 ? undefined : index;
          }
          return {
            name: asset,
            favoriteSymbolId,
            icon: coinicons[`${asset}.png`]
              ? require(`assets/icons/coinicon/${asset}.png`)
              : null,
            ...realTimeData?.[asset],
          };
        }) ?? [],
        (o) => !isUndefined(o.favoriteSymbolId),
        'desc'
      ),
    [assets, realTimeData, favoriteSymbols, localFavoriteSymbols, loggedin]
  );

  const columns = useMemo(
    () => [
      {
        header: t('Favorite Symbol'),
        accessorKey: 'favoriteSymbolId',
        enableGlobalFilter: false,
        // enableSorting: false,
        size: matchLargeScreen ? 10 : 35,
        maxSize: matchLargeScreen ? 10 : 35,
        muiTableBodyCellProps: { sx: { pl: 1 } },
        muiTableHeadCellProps: {
          sx: {
            pointerEvents: 'none',
            '& .MuiTableSortLabel-root': { display: 'none' },
          },
        },
        Cell: renderStarCell,
        Header: <span />,
      },
      {
        header: t('Name'),
        accessorKey: 'name',
        size: 50,
        muiTableBodyCellProps: { sx: { pl: { xs: 0, sm: 2 } } },
        muiTableHeadCellProps: { sx: { pl: { xs: 0, sm: 2 } } },
        Cell: renderNameCell,
        Header: renderNameHeader,
      },
      {
        header: t('Price'),
        accessorKey: 'tp',
        enableGlobalFilter: false,
        size: 50,
        Cell: renderPriceCell,
      },
      {
        header: selectedExchanges?.baseExchange.includes('UPBIT')
          ? t('KIMP')
          : t('Premium'),
        accessorKey: 'tp_close',
        enableGlobalFilter: false,
        size: 50,
        Cell: renderPremiumCell,
      },
      // {
      //   header: t('Change'),
      //   accessorKey: 'change',
      //   enableGlobalFilter: false,
      //   size: 50,
      //   Cell: ({ cell }) => formatIntlNumber(cell.getValue(), 4),
      // },
      // {
      //   header: t('52-Week High'),
      //   accessorKey: 'weekhigh',
      //   enableGlobalFilter: false,
      //   size: 50,
      // },
      // {
      //   header: t('52-Week Low'),
      //   accessorKey: 'weeklow',
      //   enableGlobalFilter: false,
      //   size: 50,
      //   Cell: ({ cell }) => formatIntlNumber(cell.getValue(), 4),
      // },
      {
        header: t('Volume (24h)'),
        accessorKey: 'atp24h',
        enableGlobalFilter: false,
        size: 50,
        Cell: ({ cell }) => formatShortNumber(cell.getValue(), 2),
      },
      {
        header: t('Expand'),
        accessorKey: 'expand',
        enableGlobalFilter: false,
        enableSorting: false,
        size: matchLargeScreen ? 10 : 35,
        maxSize: matchLargeScreen ? 10 : 35,
        muiTableBodyCellProps: { align: 'right', sx: { px: 0.5 } },
        muiTableHeadCellProps: { align: 'right' },
        Cell: renderExpandCell,
        Header: <span />,
      },
    ],
    [i18n.language, loggedin, selectedExchanges]
  );

  useEffect(() => {
    setExpanded({});
  }, [selectedExchanges]);

  return (
    <Box>
      {!matchLargeScreen && (
        <MarketExchangeSelector
          onChange={(value) => setSelectedExchanges(value)}
        />
      )}
      <MaterialReactTable
        defaultColumn={{ sortingFn: 'sortWithStarred' }}
        columns={columns}
        data={tableData}
        getRowId={(row) => row.name}
        initialState={{
          columnOrder: columns.map((col) => col.accessorKey),
          columnVisibility: {
            // isStarred: matchLargeScreen,
            // weekhigh: matchLargeScreen,
            // weeklow: matchLargeScreen,
            expand: matchLargeScreen,
            'mrt-row-expand': false,
            // 'mrt-row-select': false,
          },
          density: 'compact',
          showColumnFilters: false,
        }}
        state={{
          expanded,
          isLoading: tableData?.length === 0,
          showProgressBars:
            createFavoriteRes.isLoading || deleteFavoriteRes.isLoading,
        }}
        sortingFns={{ sortWithStarred }}
        renderDetailPanel={({ row }) => (
          <Box>
            <Collapse unmountOnExit in={row.getIsExpanded()}>
              <LightWeightKLineChart
                coinData={row.original}
                selectedExchanges={selectedExchanges}
                onAddFavoriteSymbol={handleAddFavoriteSymbol}
                onRemoveFavoriteSymbol={handleRemoveFavoriteSymbol}
                initialData={HISTORICAL_DATA}
              />
            </Collapse>
          </Box>
        )}
        renderTopToolbarCustomActions={
          matchLargeScreen
            ? () => (
                <MarketExchangeSelector
                  onChange={(value) => setSelectedExchanges(value)}
                />
              )
            : null
        }
        muiSearchTextFieldProps={{
          inputProps: {
            placeholder: t('Search {{size}} coins', {
              size: tableData?.length,
            }),
          },
        }}
        muiTableHeadCellProps={{ align: 'left' }}
        muiTableBodyCellProps={{
          align: 'left',
          sx: { fontSize: 16 },
        }}
        muiTableBodyRowProps={({ row }) => ({
          onClick: (e) => {
            if (
              e.target.classList.contains('MuiTableCell-root') &&
              !e.target.classList.contains('Mui-TableBodyCell-DetailPanel')
            )
              // debouncedHandleExpandRow({ [row.id]: !expanded[row.id] });
              setExpanded({ [row.id]: !expanded[row.id] });
          },
          sx: {
            cursor: 'pointer',
            ...(row.getIsExpanded() ||
            !isUndefined(row.original.favoriteSymbolId)
              ? {
                  bgcolor: alpha(
                    theme.palette[row.getIsExpanded() ? 'primary' : 'secondary']
                      .main,
                    0.075
                  ),
                }
              : {}),
          },
        })}
      />
    </Box>
  );
}
