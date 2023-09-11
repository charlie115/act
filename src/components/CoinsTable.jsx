import React, { Fragment, useEffect, useMemo, useState } from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Collapse from '@mui/material/Collapse';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown';
import ArrowDropUpIcon from '@mui/icons-material/ArrowDropUp';
import BlockIcon from '@mui/icons-material/Block';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDownSharp';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUpSharp';
import StarIcon from '@mui/icons-material/Star';
import StarOutlineIcon from '@mui/icons-material/StarOutline';
import SyncAltIcon from '@mui/icons-material/SyncAlt';

import debounce from 'lodash/debounce';
import orderBy from 'lodash/orderBy';

import { useSelector } from 'react-redux';

import useMediaQuery from '@mui/material/useMediaQuery';
import { styled, useTheme } from '@mui/material/styles';

import CoinsSelector from 'components/CoinsSelector';
import PeriodIntervalToggle from 'components/PeriodIntervalToggle';

import { coinicons } from 'assets/exports';

import { TRADING_PLATFORMS } from 'constants/lists';

const FROM_MARKET = ['Upbit', 'Upbit(BTC)', 'Bithumb', 'Coinone'];
const TO_MARKET = [
  'Binance BTC Market',
  'Binance USDT Market',
  'Binance BUSD Market',
  'Binance Futures USD-M Market',
  'Binance Futures BUSD Market',
];

const TBodyCell = styled(TableCell)(() => ({ borderBottom: 0 }));

const THeadCell = styled(TableCell, {
  shouldForwardProp: (prop) => prop !== 'active',
})(({ active, theme }) => ({
  color: active
    ? theme.palette.text.main
    : theme.palette.grey[theme.palette.mode === 'dark' ? '300' : '400'],
  cursor: 'pointer',
  fontSize: 11,
  fontWeight: active ? 700 : 'normal',
}));

const LightWeightPriceChart = React.lazy(() =>
  import('components/charts/LightWeightPriceChart')
);

function CoinsTable({ data, priceData }) {
  const theme = useTheme();

  const language = useSelector((state) => state.app.language);

  const [fields, setFields] = useState([]);
  const [expandedRows, setExpandedRows] = useState([]);

  const [interval, setInterval] = useState();

  const [tradingCo, setTradingCo] = useState([]);
  const [selectedTradingCo, setSelectedTradingCo] = useState(null);

  const [filteredCoins, setFilteredCoins] = useState([]);

  const [sortSetting, setSortSetting] = useState({
    sortKey: '',
    sortOrder: '',
  });

  const [fromAnchorEl, setFromAnchorEl] = React.useState(null);
  const [toAnchorEl, setToAnchorEl] = React.useState(null);

  const [fromMarket, setFromMarket] = React.useState(FROM_MARKET[0]);
  const [toMarket, setToMarket] = React.useState(TO_MARKET[0]);

  const rows = useMemo(() => {
    const parsedData =
      filteredCoins.length > 0
        ? filteredCoins.map((coin) => data[coin])
        : Object.entries(data ?? {}).map(([_, value]) => value);
    return sortSetting.sortKey
      ? orderBy(parsedData, sortSetting.sortKey, sortSetting.sortOrder)
      : parsedData;
  }, [data, filteredCoins, sortSetting]);

  useEffect(() => {
    setExpandedRows([]);
  }, [filteredCoins, sortSetting]);

  useEffect(() => {
    setFields([].map((field) => ({ label: field.getLabel(), ...field })));
    const companies = TRADING_PLATFORMS.map((comp) => ({
      label: comp.getLabel(),
      ...comp,
    }));
    setTradingCo(companies);
    setSelectedTradingCo(companies[0]);
  }, [language]);

  const matchLargeScreen = useMediaQuery('(min-width:600px)');

  const onChangeSortSetting = (sortKey) => {
    setSortSetting((state) => {
      if (state.sortKey === sortKey) {
        switch (state.sortOrder) {
          case '':
            state.sortOrder = 'asc';
            break;
          case 'asc':
            state.sortOrder = 'desc';
            break;
          case 'desc':
            state.sortKey = '';
            state.sortOrder = '';
            break;
          default:
            break;
        }
      } else {
        state.sortKey = sortKey;
        state.sortOrder = 'asc';
      }
      return state;
    });
  };

  const onRowClick = (rowId) => {
    setExpandedRows((state) =>
      state.includes(rowId)
        ? state.filter((i) => i !== rowId)
        : state.concat(rowId)
    );
  };

  const onFilterChange = debounce((value) => setFilteredCoins(value), 1000);

  return (
    <Box sx={{ p: 1 }}>
      <Stack
        useFlexGap
        direction="row"
        flexWrap="wrap"
        sx={{ alignItems: 'flex-end', justifyContent: 'space-between', mb: 2 }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <Button
            onClick={(e) => {
              setFromAnchorEl(e.currentTarget);
              setToAnchorEl(null);
            }}
            sx={{ px: 1, zIndex: toAnchorEl ? 10001 : null }}
          >
            {fromMarket}
          </Button>
          <Menu
            anchorEl={fromAnchorEl}
            open={!!fromAnchorEl}
            onClose={() => setFromAnchorEl(null)}
            variant="menu"
          >
            {FROM_MARKET.map((item) => (
              <MenuItem
                key={item}
                selected={item === fromMarket}
                onClick={() => {
                  setFromMarket(item);
                  setFromAnchorEl(null);
                }}
              >
                {item}
              </MenuItem>
            ))}
          </Menu>
          <SyncAltIcon color="secondary" fontSize="small" />
          <Button
            onClick={(e) => {
              setFromAnchorEl(null);
              setToAnchorEl(e.currentTarget);
            }}
            sx={{ px: 1, zIndex: fromAnchorEl ? 10001 : null }}
          >
            {toMarket}
          </Button>
          <Menu
            anchorEl={toAnchorEl}
            open={!!toAnchorEl}
            onClose={() => setToAnchorEl(null)}
          >
            {TO_MARKET.map((item) => (
              <MenuItem
                key={item}
                selected={item === toMarket}
                onClick={() => {
                  setToMarket(item);
                  setToAnchorEl(null);
                }}
              >
                {item}
              </MenuItem>
            ))}
          </Menu>
        </Box>
        <CoinsSelector onChange={onFilterChange} />
      </Stack>
      <TableContainer component={Paper}>
        <Table size="small" sx={{ tableLayout: 'fixed' }}>
          <TableHead>
            <TableRow>
              {/* <TableCell sx={{ p: 0, width: '3%' }} /> */}
              <TableCell width={10} sx={{ p: 0, pl: 4 }} />
              {fields.map((field) =>
                !(field.hideOnSmallScreen && !matchLargeScreen) ? (
                  <THeadCell
                    key={field.fieldKey}
                    nowrap="nowrap"
                    active={sortSetting.sortKey === field.fieldKey}
                    sx={{ ...field.headerStyle }}
                    {...field.headerProps}
                  >
                    <Stack
                      direction="row"
                      spacing={1}
                      sx={{ ...field.headerStackStyle }}
                      onClick={() => onChangeSortSetting(field.fieldKey)}
                    >
                      <Stack spacing={-1.25}>
                        <ArrowDropUpIcon
                          color={
                            sortSetting.sortKey === field.fieldKey &&
                            sortSetting.sortOrder === 'asc'
                              ? theme.palette.text.main
                              : 'secondary'
                          }
                          sx={{ fontSize: 16 }}
                        />
                        <ArrowDropDownIcon
                          color={
                            sortSetting.sortKey === field.fieldKey &&
                            sortSetting.sortOrder === 'desc'
                              ? theme.palette.text.main
                              : 'secondary'
                          }
                          sx={{ fontSize: 16 }}
                        />
                      </Stack>
                      {field.label}
                    </Stack>
                  </THeadCell>
                ) : null
              )}
            </TableRow>
          </TableHead>
          <TableBody>
            {rows?.map((row) => (
              <Fragment key={row.id}>
                <TableRow
                  hover
                  onClick={() => onRowClick(row.id)}
                  sx={{
                    cursor: 'pointer',
                    '&:last-child td, &:last-child th': { border: 0 },
                  }}
                >
                  {/* <TBodyCell align="left" sx={{ px: 0 }}>
                    <Box sx={{ display: 'flex' }}>
                      <StarIcon />
                    </Box>
                  </TBodyCell> */}
                  <TBodyCell align="left" sx={{ px: 0 }}>
                    <Stack sx={{ alignItems: 'center' }}>
                      {coinicons[`${row.name}.png`] ? (
                        <img
                          loading="lazy"
                          width="15"
                          src={require(`assets/icons/coinicon/${row.name}.png`)}
                          alt=""
                        />
                      ) : (
                        <BlockIcon color="secondary" sx={{ fontSize: 15 }} />
                      )}
                      {expandedRows.includes(row.id) ? (
                        <KeyboardArrowUpIcon fontSize="small" />
                      ) : (
                        <KeyboardArrowDownIcon fontSize="small" />
                      )}
                    </Stack>
                  </TBodyCell>
                  {fields.map((field) => {
                    const value = field.formatValue
                      ? field.formatValue(row[field.fieldKey], row, field)
                      : row[field.fieldKey];
                    return !(field.hideOnSmallScreen && !matchLargeScreen) ? (
                      <TBodyCell
                        key={field.fieldKey}
                        sx={{ ...field.cellStyle }}
                        {...field.cellProps}
                      >
                        <Stack spacing={0} {...field.stackProps}>
                          <Tooltip
                            title={
                              field.hasTooltip ? row[field.fieldKey] : null
                            }
                            placement="right-end"
                          >
                            <Typography>{value}</Typography>
                          </Tooltip>
                          <Typography
                            sx={{ color: 'secondary.main', fontSize: 11 }}
                          >
                            ...
                            {/* {field.formatValue
                              ? field.formatValue(
                                  data?.coinListPrev[i]?.[field.fieldKey],
                                  field,
                                  { t }
                                )
                              : data?.coinListPrev[i]?.[field.fieldKey]} */}
                          </Typography>
                        </Stack>
                      </TBodyCell>
                    ) : null;
                  })}
                </TableRow>
                <TableRow>
                  <TableCell colSpan={8} sx={{ p: 0 }}>
                    <Collapse unmountOnExit in={expandedRows.includes(row.id)}>
                      <Stack sx={{ mb: 1, mt: 0.5 }}>
                        <Stack
                          direction="row"
                          spacing={1}
                          sx={{ justifyContent: 'space-between', mb: 1 }}
                        >
                          <Button
                            color="secondary"
                            size="small"
                            variant="outlined"
                            startIcon={<StarIcon />}
                            sx={{ fontSize: 11, py: 0 }}
                          >
                            {row.name}
                          </Button>
                          <PeriodIntervalToggle
                            selected={interval}
                            onChange={(val) => setInterval(val)}
                          />
                          <ToggleButtonGroup
                            exclusive
                            value={selectedTradingCo?.value}
                            onChange={(e) => {
                              setSelectedTradingCo(
                                tradingCo[Number(e.target.id)]
                              );
                            }}
                            color="secondary"
                            size="small"
                          >
                            {tradingCo.map((company, idx) => (
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
                        </Stack>
                        <React.Suspense fallback={null}>
                          <LightWeightPriceChart data={priceData[row.name]} />
                        </React.Suspense>
                      </Stack>
                    </Collapse>
                  </TableCell>
                </TableRow>
              </Fragment>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}

export default React.memo(CoinsTable);
