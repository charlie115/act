import React, {
  Fragment,
  useEffect,
  useMemo,
  useState,
  useTransition,
} from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import ButtonGroup from '@mui/material/ButtonGroup';
import Collapse from '@mui/material/Collapse';
import CircularProgress from '@mui/material/CircularProgress';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import Paper from '@mui/material/Paper';

import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown';
import ArrowDropUpIcon from '@mui/icons-material/ArrowDropUp';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import BlockIcon from '@mui/icons-material/Block';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDownSharp';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUpSharp';
import SearchIcon from '@mui/icons-material/Search';
import StarIcon from '@mui/icons-material/Star';
import StarOutlineIcon from '@mui/icons-material/StarOutline';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';

import { matchSort } from 'match-sorter';
import orderBy from 'lodash/orderBy';

import { Trans, useTranslation } from 'react-i18next';
import { useDispatch, useSelector } from 'react-redux';

import { styled } from '@mui/material/styles';

import { useGetKpWebsocketDataQuery } from 'redux/api/websocket';

import ChartJsPriceChart from 'components/charts/ChartJsPriceChart';
import LightWeightPriceChart from 'components/charts/LightWeightPriceChart';
import TVRealTimeChart from 'components/trading_view/TVRealTimeChart';

import { coinicons } from 'assets/exports';

import {
  COIN_FIELDS,
  DATA_INTERVALS,
  TRADING_COMPANIES,
} from 'constants/lists';

const TBodyCell = styled(TableCell)(() => ({ borderBottom: 0 }));

const THeadCell = styled(TableCell)(({ theme }) => ({
  color: theme.palette.grey[theme.palette.mode === 'dark' ? '300' : '400'],
  cursor: 'pointer',
  fontSize: 11,
}));

function CoinsTable({ data, priceData }) {
  const { t } = useTranslation();

  const language = useSelector((state) => state.app.language);

  const [fields, setFields] = useState([]);
  const [expandedRows, setExpandedRows] = useState([]);

  const [intervals, setIntervals] = useState([]);
  const [selectedInterval, setSelectedInterval] = useState(null);

  const [tradingCo, setTradingCo] = useState([]);
  const [selectedTradingCo, setSelectedTradingCo] = useState(null);

  const [sortFilter, setSortFilter] = useState({
    sortKey: '',
    sortOrder: '',
  });

  const rows = useMemo(() => {
    const parsedData = Object.entries(data ?? {}).map(([_, value]) => value);
    return sortFilter.sortKey
      ? orderBy(parsedData, sortFilter.sortKey, sortFilter.sortOrder)
      : parsedData;
  }, [data, sortFilter]);

  useEffect(() => {
    setExpandedRows([]);
  }, [sortFilter]);

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

  const onChangeSortFilter = (sortKey) => {
    setSortFilter((state) => {
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

  return (
    <Box>
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
                  {...field.headerProps}
                  sx={
                    sortFilter.sortKey === field.fieldKey
                      ? { color: 'white.main', fontWeight: 700 }
                      : {}
                  }
                >
                  <Stack
                    direction="row"
                    spacing={1}
                    sx={{ ...field.headerStackStyle }}
                    onClick={() => onChangeSortFilter(field.fieldKey)}
                  >
                    <Stack spacing={-1.25}>
                      <ArrowDropUpIcon
                        color={
                          sortFilter.sortKey === field.fieldKey &&
                          sortFilter.sortOrder === 'asc'
                            ? 'white'
                            : 'secondary'
                        }
                        sx={{ fontSize: 16 }}
                      />
                      <ArrowDropDownIcon
                        color={
                          sortFilter.sortKey === field.fieldKey &&
                          sortFilter.sortOrder === 'desc'
                            ? 'white'
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
                              <ToggleButton
                                key={interval.value}
                                value={interval.value}
                                sx={{ fontSize: 11, py: 0 }}
                              >
                                {interval.label}
                              </ToggleButton>
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
                        <LightWeightPriceChart data={priceData[row.name]} />
                        {/* <TVRealTimeChart
                          containerId={`tv-realtime-chart-${row.name}`}
                          symbol={`${selectedTradingCo?.value}:${row.name}${selectedTradingCo?.currency}`}
                        /> */}
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
