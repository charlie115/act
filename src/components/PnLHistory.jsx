import React, { useEffect, useMemo, useRef, useState } from 'react';

import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';

import useMediaQuery from '@mui/material/useMediaQuery';
import { alpha, useTheme } from '@mui/material/styles';

import { LineType } from 'lightweight-charts';

import { useTranslation } from 'react-i18next';

import { DateTime } from 'luxon';

import groupBy from 'lodash/groupBy';
import orderBy from 'lodash/orderBy';
import sortBy from 'lodash/sortBy';
import truncate from 'lodash/truncate';

import LightWeightBaseChart from 'components/charts/LightWeightBaseChart';

import ReactTableUI from 'components/ReactTableUI';
import renderDate from 'components/tables/common/renderDate';

import formatIntlNumber from 'utils/formatIntlNumber';
import getWhiteSpaceChartData from 'utils/getWhiteSpaceChartData';

import { PERIOD_LIST } from 'constants/lists';

import PNL from 'assets/pnl-dummy.json';

export default function PnLHistory({ marketCodeCombination }) {
  const chartRef = useRef();
  const accumulatedSeriesRef = useRef();
  const normalSeriesRef = useRef();
  const quantitySeriesRef = useRef();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const { i18n, t } = useTranslation();

  const [dataType, setDataType] = useState('profit');
  const handleDataTypeChange = (event, newDataType) => setDataType(newDataType);

  const [period, setPeriod] = useState('day');
  const handlePeriodChange = (event, newPeriod) => setPeriod(newPeriod);

  const marketCodes = useMemo(
    () => ({
      targetMarketCode: marketCodeCombination.target?.value,
      originMarketCode: marketCodeCombination.origin?.value,
    }),
    [marketCodeCombination]
  );

  const format = useMemo(() => {
    switch (period) {
      case 'week':
        return "'W'WW yyyy";
      case 'month':
        return 'LLL yyyy';
      default:
        return 'LLL dd, yyyy';
    }
  }, [period]);

  const pnlDataByPeriod = useMemo(() => {
    const groupedData = groupBy(PNL, (o) =>
      DateTime.fromISO(o.datetime).startOf(period).toMillis()
    );
    return groupedData;
  }, [format, period]);

  const chartData = useMemo(() => {
    const accumulated = [];
    const normal = [];
    const quantity = [];

    let total = 0;
    const sorted = Object.keys(pnlDataByPeriod).sort();
    sorted.forEach((key, index) => {
      const items = pnlDataByPeriod[key];

      const time = DateTime.fromMillis(Number(key));
      const accumulatedValue = items.reduce(
        (acc, curr) => acc + curr.total_pnl_after_fee_kimp,
        0
      );

      total += accumulatedValue;
      normal.push({
        time: time.toMillis() / 1000,
        value: accumulatedValue,
      });
      accumulated.push({ time: time.toMillis() / 1000, value: total });
      quantity.push({ time: time.toMillis() / 1000, value: items.length });

      const timeNext = sorted[index + 1]
        ? DateTime.fromMillis(Number(sorted[index + 1]))
        : DateTime.now().startOf(period);
      const whiteSpaceData = getWhiteSpaceChartData({
        from: time,
        to: timeNext,
        interval: { quantity: 1, unit: `${period}s` },
      });
      normal.push(...whiteSpaceData.map((d) => ({ ...d, value: 0 })));
      accumulated.push(...whiteSpaceData.map((d) => ({ ...d, value: total })));
      quantity.push(...whiteSpaceData.map((d) => ({ ...d, value: 0 })));
    });
    return {
      accumulated: sortBy(accumulated, 'time'),
      normal: sortBy(normal, 'time'),
      quantity: sortBy(quantity, 'time'),
    };
  }, [pnlDataByPeriod, period, theme]);

  const tableData = useMemo(
    () =>
      orderBy(PNL, (o) => DateTime.fromISO(o.datetime).toMillis(), 'desc').map(
        (item) => ({
          ...item,
          ...(isMobile
            ? {
                uuid: truncate(item.uuid, { length: 10 }),
                trade_uuid: truncate(item.uuid, { length: 10 }),
                enter_trade_history_uuid: truncate(item.uuid, { length: 10 }),
                exit_trade_history_uuid: truncate(item.uuid, { length: 10 }),
              }
            : {}),
        })
      ),
    [isMobile]
  );

  const columns = useMemo(
    () => [
      {
        accessorKey: 'datetime',
        size: isMobile ? 30 : 120,
        header: t('Date'),
        cell: renderDate,
      },
      {
        accessorKey: 'uuid',
        size: isMobile ? 40 : 150,
        header: t('UUID'),
      },
      {
        accessorKey: 'trade_uuid',
        size: isMobile ? 40 : 150,
        header: t('Trade UUID'),
      },
      {
        accessorKey: 'enter_trade_history_uuid',
        size: isMobile ? 40 : 150,
        header: t('Enter Trade History UUID'),
      },
      {
        accessorKey: 'exit_trade_history_uuid',
        size: isMobile ? 40 : 150,
        header: t('Exit Trade History UUID'),
      },
      {
        accessorKey: 'realized_premium_gap_p',
        size: isMobile ? 30 : 80,
        header: t('Realized Premium Gap (%)'),
      },
      {
        accessorKey: 'total_currency',
        size: isMobile ? 30 : 80,
        header: t('Total Currency'),
      },
      {
        accessorKey: 'total_pnl',
        size: isMobile ? 30 : 80,
        header: t('Total PnL'),
      },
      {
        accessorKey: 'total_pnl_after_fee',
        size: isMobile ? 30 : 80,
        header: t('Total PnL After Fee'),
      },
      {
        accessorKey: 'total_pnl_after_fee_kimp',
        size: isMobile ? 30 : 80,
        header: t('Total PnL After Fee KIMP'),
      },
    ],
    [i18n.language, isMobile]
  );

  useEffect(() => {
    if (dataType === 'quantity') {
      quantitySeriesRef.current.setData(chartData.quantity);
    } else {
      accumulatedSeriesRef.current.setData(chartData.accumulated);
      normalSeriesRef.current.setData(chartData.normal);
      setTimeout(() => chartRef.current.timeScale().fitContent(), 0);
    }
  }, [chartData, dataType]);

  return (
    <Box sx={{}}>
      <Box
        component={Paper}
        sx={{ bgcolor: alpha(theme.palette.background.default, 0.85), p: 2 }}
      >
        <Box
          display="flex"
          alignItems="flex-start"
          justifyContent="space-between"
          flexDirection={{ xs: 'column', md: 'row' }}
        >
          <ToggleButtonGroup
            exclusive
            size="small"
            value={period}
            onChange={handlePeriodChange}
            aria-label="Period"
            sx={{ mb: 1 }}
          >
            {PERIOD_LIST.map((item) => (
              <ToggleButton
                key={item.value}
                value={item.value}
                sx={{ px: 2, py: 0 }}
              >
                {item.getLabel()}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
          <ToggleButtonGroup
            exclusive
            size="small"
            value={dataType}
            onChange={handleDataTypeChange}
            sx={{ mb: 1 }}
          >
            <ToggleButton value="profit" sx={{ px: 2, py: 0 }}>
              {t('Profit')}
            </ToggleButton>
            <ToggleButton value="quantity" sx={{ px: 2, py: 0 }}>
              {t('No. of Trades')}
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>
        <LightWeightBaseChart
          ref={chartRef}
          baseSeriesRef={normalSeriesRef}
          chartOptions={{
            handleScale: {
              axisPressedMouseMove: false,
              axisDoubleClickReset: false,
            },
          }}
          timeScaleOptions={{
            barSpacing: 10,
            tickMarkMaxCharacterLength: 12,
            tickMarkFormatter: (time) =>
              DateTime.fromMillis(time * 1000).toFormat(format),
          }}
          tooltipOptions={{
            enabled: true,
            dimensions: { height: 140, width: 140 },
            getInnerHTML: (seriesData, date) => {
              if (dataType !== 'profit') return null;
              let dateFormat;
              switch (period) {
                case 'week':
                  dateFormat = "'W'W yyyy";
                  break;
                case 'month':
                  dateFormat = 'LLL yyyy';
                  break;
                case 'day':
                default:
                  dateFormat = 'LLL dd, yyyy';
              }
              const accumulatedData = seriesData.get(
                accumulatedSeriesRef.current
              );
              const accumulatedProfit = accumulatedData?.value || 0;
              const normalData = seriesData.get(normalSeriesRef.current);
              const normalProfit = normalData?.value || 0;
              return `
                  <div style="color: ${
                    theme.palette.text.main
                  }">${DateTime.fromMillis(date).toFormat(dateFormat)}</div>
                  <hr />
                  <small>${t('Accumulated')}</small>
                  <div style="font-size: 16px; margin: 0; margin-bottom: 2px; color: ${
                    theme.palette.accent.main
                  }">${formatIntlNumber(accumulatedProfit, 3, 1)}</div>
                  <small>${t('Profit')}</small>
                  <div style="font-size: 16px; margin: 0; color: ${
                    theme.palette.primary.main
                  }">${formatIntlNumber(normalProfit, 3, 1)}</div>`;
            },
            getCoordinate: (seriesData) => {
              if (dataType !== 'profit') return null;
              const seriesValue = seriesData.get(accumulatedSeriesRef.current);
              return seriesValue?.value || seriesValue?.close
                ? accumulatedSeriesRef.current.priceToCoordinate(
                    seriesValue?.value || seriesValue?.close
                  )
                : null;
            },
          }}
          dependencies={[dataType, format, period]}
          interval={{ quantity: 1, unit: period }}
          onReady={(baseChartRef) => {
            if (dataType === 'profit') {
              accumulatedSeriesRef.current = baseChartRef.current.addAreaSeries(
                {
                  priceScaleId: 'left',
                  lineColor: theme.palette.accent.main,
                  lineType: LineType.Curved,
                  lineWidth: 1,
                  pointMarkersVisible: true,
                  pointMarkersRadius: 2,
                  topColor: alpha(theme.palette.accent.main, 0.4),
                  bottomColor: alpha(theme.palette.accent.main, 0.1),
                  scaleMargins: { top: 0.8, bottom: 0 },
                }
              );
              normalSeriesRef.current = baseChartRef.current.addLineSeries({
                priceScaleId: 'left',
                lineColor: theme.palette.accent.main,
                lineType: LineType.Curved,
                lineWidth: 1,
                pointMarkersVisible: true,
                pointMarkersRadius: 2,
                scaleMargins: { top: 1, bottom: 0 },
              });
            } else
              quantitySeriesRef.current =
                baseChartRef.current.addHistogramSeries({
                  color: theme.palette.primary.main,
                  priceScaleId: 'left',
                  priceFormat: {
                    type: 'custom',
                    formatter: (value) => parseInt(value, 10),
                  },
                });
          }}
        />
      </Box>
      <Box
        component={Paper}
        sx={{
          bgcolor: alpha(theme.palette.background.default, 0.85),
          mt: 2,
          p: { xs: 0.5, md: 2 },
        }}
      >
        <ReactTableUI
          enableTablePaginationUI
          // ref={tableRef}
          columns={columns}
          data={tableData}
          // options={{
          //   state: { expanded, pagination },
          //   onExpandedChange: (newExpanded) => setExpanded(newExpanded()),
          //   onPaginationChange: setPagination,
          //   meta: { theme, isMobile, expandIcon: InsightsIcon },
          // }}
          // renderSubComponent={renderSubComponent}
          getCellProps={() => ({ onClick: () => {}, sx: { height: 40 } })}
          getRowProps={(row) => ({
            onClick: () => row.toggleExpanded(!row.getIsExpanded()),
            sx: {
              cursor: 'pointer',
              ...(row.getIsExpanded()
                ? { bgcolor: theme.palette.background.paper }
                : {}),
            },
          })}
          //   showProgressBar={isLoading}
          //   isLoading={isLoading}
        />
      </Box>
    </Box>
  );
}
