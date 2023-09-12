import React, { useEffect, useMemo, useState } from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Collapse from '@mui/material/Collapse';
import Grid from '@mui/material/Grid';
import LinearProgress from '@mui/material/LinearProgress';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import Stack from '@mui/material/Stack';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';

import BlockIcon from '@mui/icons-material/Block';
import InsightsIcon from '@mui/icons-material/Insights';
import StarIcon from '@mui/icons-material/Star';
import StarOutlineIcon from '@mui/icons-material/StarOutline';

import { alpha, useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

import { useTranslation } from 'react-i18next';

import formatIntlNumber from 'utils/formatIntlNumber';
import formatShortNumber from 'utils/formatShortNumber';

import MarketExchangeSelector from 'components/MarketExchangeSelector';
import MaterialReactTable from 'components/MaterialReactTable';
import PeriodIntervalToggle from 'components/PeriodIntervalToggle';

import { TRADING_PLATFORMS } from 'constants/lists';

const LightWeightPriceChart = React.lazy(() =>
  import('components/charts/LightWeightPriceChart')
);

export default function RealTimeCoinsTable({ realTimeData, seriesData }) {
  const { i18n, t } = useTranslation();

  const theme = useTheme();

  const [expanded, setExpanded] = useState({});

  const [selectedInterval, setSelectedInterval] = useState(null);

  const [tradingPlatforms, setTradingPlatforms] = useState([]);
  const [selectedTradingPlatform, setSelectedTradingPlatform] = useState(null);

  const matchLargeScreen = useMediaQuery('(min-width:600px)');

  const renderName = (value, icon) => (
    <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
      {icon ? (
        <img loading="lazy" width="15" src={icon} alt="" />
      ) : (
        <BlockIcon color="secondary" sx={{ fontSize: 15 }} />
      )}
      <span>{value}</span>
    </Stack>
  );

  const renderNameHeader = (header) => (
    <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
      <Box sx={{ width: '15px' }} />
      {header}
    </Stack>
  );

  const renderExpandIcon = (row) => (
    <InsightsIcon
      onClick={() =>
        setExpanded({ ...expanded, [row.id]: !row.getIsExpanded() })
      }
      color={row.getIsExpanded() ? 'info' : ''}
      fontSize="small"
    />
  );

  const renderStarIcon = (isStarred) =>
    isStarred ? (
      <StarIcon fontSize="small" />
    ) : (
      <StarOutlineIcon
        fontSize="small"
        onClick={() => console.log('starred')}
      />
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
        Cell: ({ cell }) => renderStarIcon(cell.getValue()),
        Header: <span />,
      },
      {
        header: t('Name'),
        accessorKey: 'name',
        size: 50,
        muiTableBodyCellProps: { align: 'left', sx: { pl: { xs: 0, sm: 2 } } },
        muiTableHeadCellProps: { align: 'left', sx: { pl: { xs: 0, sm: 2 } } },
        Cell: ({ renderedCellValue, row }) =>
          renderName(renderedCellValue, row.original.icon),
        Header: ({ column }) => renderNameHeader(column.columnDef.header),
      },
      {
        header: t('Price'),
        accessorKey: 'price',
        enableGlobalFilter: false,
        size: 50,
        Cell: ({ cell }) =>
          formatIntlNumber(cell.getValue(), cell.getValue() > 0 ? 0 : 4),
      },
      {
        header: t('KIMP'),
        accessorKey: 'kimp',
        enableGlobalFilter: false,
        size: 50,
        Cell: ({ cell }) => formatIntlNumber(cell.getValue(), 4),
        // formatIntlNumber(cell.getValue(), cell.getValue() > 0 ? 2 : 4),
      },
      {
        header: t('Change'),
        accessorKey: 'change',
        enableGlobalFilter: false,
        size: 50,
        Cell: ({ cell }) => formatIntlNumber(cell.getValue(), 4),
      },
      {
        header: t('52-Week High'),
        accessorKey: 'weekhigh',
        enableGlobalFilter: false,
        size: 50,
      },
      {
        header: t('52-Week Low'),
        accessorKey: 'weeklow',
        enableGlobalFilter: false,
        size: 50,
        Cell: ({ cell }) => formatIntlNumber(cell.getValue(), 4),
      },
      {
        header: t('Volume'),
        accessorKey: 'volume',
        enableGlobalFilter: false,
        size: 50,
        Cell: ({ cell }) => formatShortNumber(cell.getValue(), 1),
      },
      {
        header: t('Expand'),
        accessorKey: 'expand',
        enableGlobalFilter: false,
        size: matchLargeScreen ? 10 : 35,
        maxSize: matchLargeScreen ? 10 : 35,
        muiTableBodyCellProps: { sx: { px: 0.5 } },
        muiTableHeadCellProps: { sx: { pointerEvents: 'none', pr: 0 } },
        Cell: ({ row }) => renderExpandIcon(row),
        Header: <span />,
      },
    ],
    [i18n.language]
  );

  useEffect(() => {
    const platforms = TRADING_PLATFORMS.map((item) => ({
      label: item.getLabel(),
      ...item,
    }));
    setTradingPlatforms(platforms);
    setSelectedTradingPlatform(platforms[0]);
  }, [i18n.language]);

  return (
    <Box>
      {!matchLargeScreen && (
        <MarketExchangeSelector onChange={(value) => console.log(value)} />
      )}
      <MaterialReactTable
        columns={columns}
        data={realTimeData}
        initialState={{
          columnOrder: columns.map((col) => col.accessorKey),
          columnVisibility: {
            isStarred: matchLargeScreen,
            weekhigh: matchLargeScreen,
            weeklow: matchLargeScreen,
            expand: matchLargeScreen,
            'mrt-row-expand': false, // matchLargeScreen,
          },
          showColumnFilters: false,
        }}
        state={{ expanded, isLoading: realTimeData.length === 0 }}
        renderDetailPanel={({ row }) => (
          <Box>
            <Grid container sx={{ mb: 3 }}>
              <Grid item xs={3} sm={3}>
                <Button
                  color="secondary"
                  size="small"
                  variant="outlined"
                  startIcon={
                    row.original.isStarred ? <StarIcon /> : <StarOutlineIcon />
                  }
                  sx={{ fontSize: 11, px: 0.5, py: 0 }}
                >
                  {row.original.name}
                </Button>
              </Grid>
              <Grid item xs={3} sm={6}>
                <PeriodIntervalToggle
                  value={selectedInterval}
                  onChange={(value) => setSelectedInterval(value)}
                />
              </Grid>
              <Grid item xs={6} sm={3}>
                <ToggleButtonGroup
                  exclusive
                  value={selectedTradingPlatform?.value}
                  onChange={(e) => {
                    setSelectedTradingPlatform(
                      tradingPlatforms[Number(e.target.id)]
                    );
                    e.stopPropagation();
                  }}
                  color="secondary"
                  size="small"
                >
                  {tradingPlatforms.map((company, idx) => (
                    <ToggleButton
                      key={company.value}
                      id={idx}
                      value={company.value}
                      sx={{ fontSize: 11, py: 0 }}
                    >
                      {company.label}
                    </ToggleButton>
                  ))}
                </ToggleButtonGroup>
              </Grid>
            </Grid>
            <Collapse unmountOnExit in={row.getIsExpanded()}>
              <React.Suspense fallback={<LinearProgress />}>
                <LightWeightPriceChart
                  data={seriesData[row.original.name] || []}
                />
              </React.Suspense>
            </Collapse>
          </Box>
        )}
        renderTopToolbarCustomActions={
          matchLargeScreen
            ? () => (
                <MarketExchangeSelector
                  onChange={(value) => console.log(value)}
                />
              )
            : null
        }
        muiExpandButtonProps={({ row }) => ({
          onClick: () =>
            setExpanded({ ...expanded, [row.id]: !expanded[row.id] }),
        })}
        muiTableHeadCellProps={{ align: 'right' }}
        muiTableBodyCellProps={{ align: 'right', sx: { fontSize: 13 } }}
        muiTableBodyRowProps={({ row }) => ({
          onClick: (e) => {
            if (
              e.target.classList.contains('MuiTableCell-root') &&
              !e.target.classList.contains('Mui-TableBodyCell-DetailPanel')
            )
              setExpanded({ ...expanded, [row.id]: !expanded[row.id] });
          },
          sx: {
            cursor: 'pointer',
            ...(row.getIsExpanded()
              ? { borderBottomColor: alpha(theme.palette.primary.main, 0.9) }
              : {}),
          },
        })}
      />
    </Box>
  );
}
