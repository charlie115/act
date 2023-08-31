import React, { Fragment, useEffect, useMemo, useState } from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Collapse from '@mui/material/Collapse';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown';
import ArrowDropUpIcon from '@mui/icons-material/ArrowDropUp';
import BlockIcon from '@mui/icons-material/Block';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDownSharp';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUpSharp';
import StarIcon from '@mui/icons-material/Star';
import StarOutlineIcon from '@mui/icons-material/StarOutline';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';

import debounce from 'lodash/debounce';
import orderBy from 'lodash/orderBy';

import { useSelector } from 'react-redux';

import { styled, useTheme } from '@mui/material/styles';

import CoinsSelector from 'components/CoinsSelector';

import { coinicons } from 'assets/exports';

import {
  COIN_FIELDS,
  DATA_INTERVALS,
  TRADING_COMPANIES,
} from 'constants/lists';

const IntervalBtn = styled(ToggleButton)(() => ({ textTransform: 'none' }));

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

  const [intervals, setIntervals] = useState([]);
  const [selectedInterval, setSelectedInterval] = useState(null);

  const [tradingCo, setTradingCo] = useState([]);
  const [selectedTradingCo, setSelectedTradingCo] = useState(null);

  const [filteredCoins, setFilteredCoins] = useState([]);

  const [sortSetting, setSortSetting] = useState({
    sortKey: '',
    sortOrder: '',
  });

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
  }, [sortSetting]);

  useEffect(() => {
    setFields(
      COIN_FIELDS.map((field) => ({ label: field.getLabel(), ...field }))
    );
    setIntervals(
      DATA_INTERVALS.map((interval) => ({
        label: interval.getLabel(),
        ...interval,
      }))
    );
    const companies = TRADING_COMPANIES.map((comp) => ({
      label: comp.getLabel(),
      ...comp,
    }));
    setTradingCo(companies);
    setSelectedTradingCo(companies[0]);
  }, [language]);

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
    <Box>
      <CoinsSelector onChange={onFilterChange} />
      <TableContainer component={Paper}>
        <Table size="small" sx={{ tableLayout: 'fixed' }}>
          <TableHead>
            <TableRow>
              {/* <TableCell sx={{ p: 0, width: '3%' }} /> */}
              <TableCell sx={{ p: 0, width: '3%' }} />
              {fields.map((field) => (
                <THeadCell
                  key={field.fieldKey}
                  nowrap="nowrap"
                  active={sortSetting.sortKey === field.fieldKey}
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
              ))}
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
                  {fields.map((field) => (
                    <TBodyCell key={field.fieldKey} {...field.cellProps}>
                      <Stack spacing={0} {...field.stackProps}>
                        <Tooltip
                          title={field.hasTooltip ? row[field.fieldKey] : null}
                          placement="right-end"
                        >
                          <Typography>
                            {field.formatValue
                              ? field.formatValue(row[field.fieldKey], field)
                              : row[field.fieldKey]}
                          </Typography>
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
                  ))}
                </TableRow>
                <TableRow>
                  <TableCell colSpan={8} sx={{ p: 0 }}>
                    <Collapse unmountOnExit in={expandedRows.includes(row.id)}>
                      <Stack sx={{ mb: 1, mt: 0.5 }}>
                        <Box
                          sx={{
                            display: 'flex',
                            flexDirection: 'row',
                            justifyContent: 'space-between',
                            mb: 1,
                          }}
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
                          <ToggleButtonGroup
                            exclusive
                            value={selectedInterval}
                            onChange={(e, newInterval) =>
                              setSelectedInterval(newInterval)
                            }
                            color="secondary"
                            size="small"
                          >
                            {intervals.map((interval) => (
                              <IntervalBtn
                                key={interval.value}
                                value={interval.value}
                                sx={{ fontSize: 11, py: 0 }}
                              >
                                {interval.label}
                              </IntervalBtn>
                            ))}
                          </ToggleButtonGroup>
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
                        </Box>
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
