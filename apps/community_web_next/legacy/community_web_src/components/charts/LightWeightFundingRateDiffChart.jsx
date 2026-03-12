import React, { useEffect, useMemo, useState, useRef } from 'react';

import Box from '@mui/material/Box';
import Card from '@mui/material/Card';

import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

import { LineType } from 'lightweight-charts';

import { useGetFundingRateQuery } from 'redux/api/drf/infocore';

import { useSelector } from 'react-redux';

import orderBy from 'lodash/orderBy';

import { DateTime } from 'luxon';

import { useTranslation } from 'react-i18next';

import formatIntlNumber from 'utils/formatIntlNumber';

import { DATE_FORMAT_API_QUERY, USER_ROLE } from 'constants';

import LightWeightBaseChart from './LightWeightBaseChart';

export default function LightWeightFundingRateDiffChart({
  baseAsset,
  marketCodes,
  subtrahend,
}) {
  const chartRef = useRef();

  const lineSeriesRef = useRef();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const { i18n, t } = useTranslation();

  const { timezone: tz } = useSelector((state) => state.app);
  const { loggedin, user } = useSelector((state) => state.auth);
  const isAuthorized = loggedin && user.role !== USER_ROLE.visitor;

  const [data, setData] = useState();
  const [startFundingTime, setStartFundingTime] = useState();
  const [endFundingTime, setEndFundingTime] = useState();

  const { data: apiTargetData, isFetching: isFetchingTarget } =
    useGetFundingRateQuery({
      baseAsset,
      startFundingTime,
      endFundingTime,
      tz,
      marketCode: marketCodes.targetMarketCode,
      lastN: -1,
    });
  const { data: apiOriginData, isFetching: isFetchingOrigin } =
    useGetFundingRateQuery({
      baseAsset,
      startFundingTime,
      endFundingTime,
      tz,
      marketCode: marketCodes.originMarketCode,
      lastN: -1,
    });

  const chartData = useMemo(
    () =>
      orderBy(
        Object.keys(data ?? {}),
        (o) => DateTime.fromISO(o).toMillis(),
        'asc'
      ).map((item) => {
        let value;
        if (subtrahend === 'origin')
          value =
            (data[item].target.funding_rate - data[item].origin.funding_rate) *
            100;
        else
          value =
            (data[item].origin.funding_rate - data[item].target.funding_rate) *
            100;
        return {
          time:
            DateTime.fromISO(data[item].target.funding_time).toMillis() / 1000,
          value,
        };
      }),
    [data, subtrahend]
  );

  useEffect(() => {
    if (apiTargetData?.[baseAsset] && apiOriginData?.[baseAsset]) {
      setData((state) => {
        apiTargetData?.[baseAsset]?.forEach((target) => {
          if (!state) state = {};
          if (!state[target.funding_time]) {
            const origin = apiOriginData?.[baseAsset]?.find(
              (o) => o.funding_time === target.funding_time
            );
            if (origin)
              state[target.funding_time] = {
                target,
                origin,
              };
          }
        });
        return state;
      });
    }
  }, [apiTargetData?.[baseAsset], apiOriginData?.[baseAsset]]);

  useEffect(() => {
    lineSeriesRef.current.setData(chartData);
    chartRef.current.timeScale().fitContent();
  }, [chartData]);

  useEffect(() => {
    chartRef.current.applyOptions({ layout: { fontSize: isMobile ? 8 : 11 } });
  }, [isMobile, i18n.language]);

  useEffect(() => {
    lineSeriesRef.current.applyOptions({ title: t('Funding Rate Difference') });
  }, [i18n.language]);

  return (
    <Card onClick={(e) => e.stopPropagation()} sx={{ borderRadius: 0 }}>
      <Box sx={{ bgcolor: 'background.paper' }}>
        <LightWeightBaseChart
          ref={chartRef}
          baseSeriesRef={lineSeriesRef}
          chartOptions={{
            crosshair: {
              horzLine: { visible: false, labelVisible: false },
              vertLine: { labelVisible: false },
            },
            handleScale: isAuthorized,
            handleScroll: isAuthorized,
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
              <div style="color: ${
                theme.palette.primary.main
              }">${baseAsset}</div>
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
          isLoading={isFetchingTarget || isFetchingOrigin}
          onBarsInfoChanged={({ start, end }) => {
            if (!(isFetchingTarget || isFetchingOrigin)) {
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
              title: t('Funding Rate Diff'),
            });
          }}
        />
      </Box>
    </Card>
  );
}
