import React, { useEffect, useMemo, useState, useRef } from 'react';

import Box from '@mui/material/Box';
import Card from '@mui/material/Card';

import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

import { LineType } from 'lightweight-charts';

import { useGetFundingRateQuery } from 'redux/api/drf/infocore';

import { useSelector } from 'react-redux';

import orderBy from 'lodash/orderBy';
import uniqBy from 'lodash/uniqBy';

import { DateTime } from 'luxon';

import { useTranslation } from 'react-i18next';

import formatIntlNumber from 'utils/formatIntlNumber';

import { DATE_FORMAT_API_QUERY } from 'constants';

import LightWeightBaseChart from './LightWeightBaseChart';

export default function LightWeightFundingRateChart({
  symbol,
  baseAsset,
  marketCode,
}) {
  const chartRef = useRef();

  const lineSeriesRef = useRef();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const { i18n, t } = useTranslation();

  const { timezone: tz } = useSelector((state) => state.app);

  const [data, setData] = useState([]);
  const [startFundingTime, setStartFundingTime] = useState();
  const [endFundingTime, setEndFundingTime] = useState();

  const { data: apiData, isFetching } = useGetFundingRateQuery({
    baseAsset,
    marketCode,
    startFundingTime,
    endFundingTime,
    tz,
    past: true,
  });

  const chartData = useMemo(
    () =>
      data.map((item) => ({
        time: DateTime.fromISO(item.funding_time).toMillis() / 1000,
        value: item.funding_rate * 100,
      })) ?? [],
    [data]
  );

  useEffect(() => {
    setData((state) =>
      orderBy(
        uniqBy([...(apiData?.[baseAsset] || []), ...state], 'funding_time'),
        (o) => DateTime.fromISO(o.funding_time).toMillis(),
        'asc'
      )
    );
  }, [apiData?.[baseAsset]]);

  useEffect(() => {
    lineSeriesRef.current.setData(chartData);
    chartRef.current.timeScale().fitContent();
  }, [chartData]);

  useEffect(() => {
    chartRef.current.applyOptions({ layout: { fontSize: isMobile ? 8 : 11 } });
  }, [isMobile, i18n.language]);

  useEffect(() => {
    lineSeriesRef.current.applyOptions({ title: t('Price') });
  }, [i18n.language]);

  return (
    <Card onClick={(e) => e.stopPropagation()} sx={{ borderRadius: 0 }}>
      <Box sx={{ bgcolor: 'background.paper' }}>
        <LightWeightBaseChart
          ref={chartRef}
          baseSeriesRef={lineSeriesRef}
          chartOptions={{
            crosshair: {
              // hide the horizontal crosshair line
              horzLine: {
                visible: false,
                labelVisible: false,
              },
              // hide the vertical crosshair label
              vertLine: {
                labelVisible: false,
              },
            },
          }}
          tooltipOptions={{
            enabled: true,
            getInnerHTML: (seriesData, date) => {
              const currentData = seriesData.get(lineSeriesRef.current);
              if (!currentData) return null;
              const price =
                currentData.value !== undefined
                  ? currentData.value
                  : currentData.close;
              return `
              <div style="color: ${theme.palette.primary.main}">${
                symbol || baseAsset
              }</div>
              <div style="font-size: 18px; margin: 4px 0px; color: ${
                theme.palette.text.main
              }">${formatIntlNumber(price, 3, 1)}<small>%</small></div>
              <div style="font-size: 10px; color: ${
                theme.palette.text.main
              }">${DateTime.fromMillis(date).toFormat('DD HH:mm:ss')}</div>`;
            },
            getCoordinate: (seriesData) => {
              const seriesValue = seriesData.get(lineSeriesRef.current);
              return seriesValue?.value || seriesValue?.close
                ? lineSeriesRef.current.priceToCoordinate(
                    seriesValue?.value || seriesValue?.close
                  )
                : null;
            },
          }}
          interval={{ quantity: 3600, unit: 'seconds' }}
          isLoading={isFetching}
          onBarsInfoChanged={({ start, end }) => {
            if (!isFetching) {
              setEndFundingTime(end.toFormat(DATE_FORMAT_API_QUERY));
              setStartFundingTime(
                start.startOf('minute').toFormat(DATE_FORMAT_API_QUERY)
              );
            }
          }}
          onReady={(ref) => {
            lineSeriesRef.current = ref.current.addLineSeries({
              priceScaleId: 'left',
              color: theme.palette.primary.main,
              crosshairMarkerVisible: false,
              lineType: LineType.Curved,
              lineWidth: 1,
              pointMarkersVisible: true,
              pointMarkersRadius: 4,
              priceFormat: {
                minMove: 0.001,
                type: 'custom',
                formatter: (price) => `${formatIntlNumber(price, 3, 1)}%`,
              },
              title: t('Funding Rate'),
            });
          }}
        />
      </Box>
    </Card>
  );
}
