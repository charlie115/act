import React, { useEffect, useMemo, useRef, useState } from 'react';

import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import FormHelperText from '@mui/material/FormHelperText';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';

import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

import { LineType } from 'lightweight-charts';

import { useGetFundingRateQuery } from 'redux/api/drf/infocore';
import { useSelector } from 'react-redux';

import orderBy from 'lodash/orderBy';

import { DateTime } from 'luxon';

import { useTranslation } from 'react-i18next';

import { useDebounce } from '@uidotdev/usehooks';

import formatIntlNumber from 'utils/formatIntlNumber';

import { USER_ROLE } from 'constants';

import LightWeightBaseChart from './LightWeightBaseChart';

export default function LightWeightAvgFundingRateDiffChart({
  baseAsset,
  marketCodes,
  subtrahend,
}) {
  const chartRef = useRef();

  const lineSeriesRef = useRef();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const { i18n, t } = useTranslation();

  const [n, setN] = useState(3);
  const debouncedN = useDebounce(n, 1000);

  const { timezone: tz } = useSelector((state) => state.app);

  const { loggedin, user } = useSelector((state) => state.auth);
  const isAuthorized = loggedin && user.role !== USER_ROLE.visitor;

  const [data, setData] = useState();
  const [output, setOutput] = useState();

  const [error, setError] = useState();

  const { data: apiTargetData, isFetching: isFetchingTarget } =
    useGetFundingRateQuery(
      {
        baseAsset,
        tz,
        marketCode: marketCodes.targetMarketCode,
        lastN: debouncedN,
      },
      { skip: error }
    );
  const { data: apiOriginData, isFetching: isFetchingOrigin } =
    useGetFundingRateQuery(
      {
        baseAsset,
        tz,
        marketCode: marketCodes.originMarketCode,
        lastN: debouncedN,
      },
      { skip: error }
    );

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
      const fundingRateData = {};
      apiTargetData?.[baseAsset]?.forEach((target) => {
        if (!fundingRateData[target.funding_time]) {
          const origin = apiOriginData?.[baseAsset]?.find(
            (o) => o.funding_time === target.funding_time
          );
          if (origin)
            fundingRateData[target.funding_time] = {
              target,
              origin,
            };
        }
      });
      setData(fundingRateData);
    }
  }, [apiTargetData?.[baseAsset], apiOriginData?.[baseAsset]]);

  useEffect(() => {
    lineSeriesRef.current.setData(chartData);
    chartRef.current.timeScale().fitContent();

    if (chartData && chartData.length > 0) {
      const sum = chartData?.reduce((acc, item) => acc + item.value, 0);
      setOutput(sum / chartData.length);
    }
  }, [chartData]);

  useEffect(() => {
    if (!n || n < 3 || n > 100) setError(true);
    else setError(false);
  }, [n]);

  useEffect(() => {
    chartRef.current.applyOptions({ layout: { fontSize: isMobile ? 8 : 11 } });
  }, [isMobile, i18n.language]);

  useEffect(() => {
    lineSeriesRef.current.applyOptions({ title: t('Funding Rate Difference') });
  }, [i18n.language]);

  return (
    <>
      <Stack
        alignItems="center"
        direction="row"
        justifyContent="center"
        spacing={3}
        sx={{ p: 1 }}
      >
        <Box>
          <TextField
            id="n-value"
            label="N"
            variant="outlined"
            type="number"
            error={error}
            value={`${n}`}
            onChange={(e) => {
              if (e.target.value) {
                const value = parseInt(e.target.value, 10);
                setN(value);
              } else setN();
            }}
            inputProps={{ sx: { p: 1.25 } }}
          />
          <FormHelperText error>
            {error &&
              t('Value must be between {{min}}~{{max}}', { min: 0, max: 100 })}
          </FormHelperText>
        </Box>
        <Box sx={{ mt: '-5px!important' }}>
          <Typography sx={{ color: 'grey.500', fontSize: 10 }}>
            {t('Avg Funding Rate Difference')}
          </Typography>
          <Typography variant="h5">
            {error ? '-' : formatIntlNumber(output, 5)}
          </Typography>
        </Box>
      </Stack>
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
    </>
  );
}
