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

import { useSelector } from 'react-redux';

import { useGetWsCoinsQuery } from 'redux/api/websocket';

import debounce from 'lodash/debounce';

import formatIntlNumber from 'utils/formatIntlNumber';
import formatShortNumber from 'utils/formatShortNumber';

import LightWeightKLineChart from 'components/charts/LightWeightKLineChart';
import MarketExchangeSelector from 'components/MarketExchangeSelector';
import MaterialReactTable from 'components/MaterialReactTable';

import { coinicons } from 'assets/exports';

const LightWeightPriceChart = React.lazy(() =>
  import('components/charts/LightWeightPriceChart')
);

const REALTIME_INTERVAL_KEY = '1T';

const HISTORICAL_DATA = [];

export default function RealTimeCoinsTable() {
  const { i18n, t } = useTranslation();

  const theme = useTheme();

  const [expanded, setExpanded] = useState({});

  const [selectedExchanges, setSelectedExchanges] = useState(null);

  // const { data } = useGetWsCoinsQuery(
  //   { ...selectedExchanges, period: selectedInterval },
  //   { skip: !selectedExchanges || selectedInterval === REALTIME_INTERVAL_KEY }
  // );

  const { assets } = useSelector((state) => state.websocket);

  const { data: realTimeData } = useGetWsCoinsQuery(
    { ...selectedExchanges, period: REALTIME_INTERVAL_KEY },
    { skip: !selectedExchanges }
  );

  const matchLargeScreen = useMediaQuery('(min-width:600px)');

  const handleExpandRow = (newExpanded) => setExpanded(newExpanded);
  const debouncedHandleExpandRow = useCallback(
    debounce(handleExpandRow, 500, {
      leading: true,
      trailing: true,
    }),
    []
  );

  const renderNameCell = ({ renderedCellValue, row }) => (
    <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
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

  const renderStarCell = ({ cell }) =>
    cell.getValue() ? (
      <StarIcon fontSize="small" />
    ) : (
      <StarOutlineIcon
        fontSize="small"
        onClick={() => console.log('starred')}
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

  const tableData = useMemo(
    () =>
      assets
        // .sort()
        ?.map((asset) => ({
          base_asset: asset,
          icon: coinicons[`${asset}.png`]
            ? require(`assets/icons/coinicon/${asset}.png`)
            : null,
          ...realTimeData[asset],
        })) ?? [],
    [assets, realTimeData]
  );

  const columns = useMemo(
    () => [
      {
        header: t('Star'),
        accessorKey: 'isStarred',
        enableGlobalFilter: false,
        size: matchLargeScreen ? 10 : 35,
        maxSize: matchLargeScreen ? 10 : 35,
        // muiTableBodyCellProps: { sx: { pr: 0 } },
        // muiTableHeadCellProps: { sx: { pointerEvents: 'none', pr: 0 } },
        Cell: renderStarCell,
        Header: <span />,
      },
      {
        header: t('Name'),
        accessorKey: 'base_asset',
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
        // formatIntlNumber(cell.getValue(), cell.getValue() > 0 ? 2 : 4),
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
        size: matchLargeScreen ? 10 : 35,
        maxSize: matchLargeScreen ? 10 : 35,
        muiTableBodyCellProps: { align: 'right', sx: { px: 0.5 } },
        muiTableHeadCellProps: {
          align: 'right',
          sx: { pointerEvents: 'none', pr: 0 },
        },
        Cell: renderExpandCell,
        Header: <span />,
      },
    ],
    [i18n.language, selectedExchanges]
  );

  useEffect(() => {
    debouncedHandleExpandRow({});
  }, [selectedExchanges]);

  return (
    <Box>
      {!matchLargeScreen && (
        <MarketExchangeSelector
          onChange={(value) => setSelectedExchanges(value)}
        />
      )}
      <MaterialReactTable
        columns={columns}
        data={tableData}
        getRowId={(row) => row.base_asset}
        initialState={{
          columnOrder: columns.map((col) => col.accessorKey),
          columnVisibility: {
            isStarred: matchLargeScreen,
            // weekhigh: matchLargeScreen,
            // weeklow: matchLargeScreen,
            expand: matchLargeScreen,
            'mrt-row-expand': false, // matchLargeScreen,
          },
          showColumnFilters: false,
        }}
        state={{ expanded, isLoading: tableData?.length === 0 }}
        renderDetailPanel={({ row }) => (
          <Box>
            <Collapse unmountOnExit in={row.getIsExpanded()}>
              <LightWeightKLineChart
                coinData={row.original}
                selectedExchanges={selectedExchanges}
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
              debouncedHandleExpandRow({ [row.id]: !expanded[row.id] });
            // setExpanded({ ...expanded, [row.id]: !expanded[row.id] });
          },
          sx: {
            cursor: 'pointer',
            ...(row.getIsExpanded()
              ? { bgcolor: alpha(theme.palette.primary.main, 0.075) }
              : {}),
          },
        })}
      />
    </Box>
  );
}
