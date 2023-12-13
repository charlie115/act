import React, {
  useCallback,
  useEffect,
  useMemo,
  useState,
  useRef,
} from 'react';

import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import IconButton from '@mui/material/IconButton';
import LinearProgress from '@mui/material/LinearProgress';

import ArrowForwardIosIcon from '@mui/icons-material/ArrowForwardIos';

import { alpha, useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

import { createChart, LineType } from 'lightweight-charts';

import { useGetFundingRateQuery } from 'redux/api/drf/infocore';

import { useSelector } from 'react-redux';

import debounce from 'lodash/debounce';
import orderBy from 'lodash/orderBy';
import uniqBy from 'lodash/uniqBy';

import { DateTime } from 'luxon';

import { usePrevious } from '@uidotdev/usehooks';
import { useTranslation } from 'react-i18next';

import formatIntlNumber from 'utils/formatIntlNumber';

import { DATE_FORMAT_API_QUERY } from 'constants';

const CHART_HEIGHT = 250;

export default function LightWeightFundingRateChart({
  symbol,
  baseAsset,
  marketCode,
}) {
  const chartContainerRef = useRef();
  const chartRef = useRef();

  const lineSeriesRef = useRef();

  const tooltipRef = useRef();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const { i18n, t } = useTranslation();

  const { timezone: tz } = useSelector((state) => state.app);

  const [barsInfo, setBarsInfo] = useState(null);

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
        time: DateTime.fromISO(item.funding_time).toMillis(),
        value: item.funding_rate * 100,
      })) ?? [],
    [data]
  );

  const onCrosshairMove = (param) => {
    if (
      param.point === undefined ||
      !param.time ||
      param.point.x < 0 ||
      param.point.x > chartContainerRef.current.clientWidth ||
      param.point.y < 0 ||
      param.point.y > chartContainerRef.current.clientHeight
    )
      tooltipRef.current.style.display = 'none';
    else {
      const dateStr = param.time;
      tooltipRef.current.style.display = 'block';
      const currentData = param.seriesData.get(lineSeriesRef.current);
      const price =
        currentData.value !== undefined ? currentData.value : currentData.close;
      tooltipRef.current.innerHTML = `
        <div style="color: ${theme.palette.primary.main}">${symbol}</div>
        <div style="font-size: 18px; margin: 4px 0px; color: ${
          theme.palette.text.main
        }">${formatIntlNumber(price, 3, 1)}<small>%</small></div>
        <div style="font-size: 10px; color: ${
          theme.palette.text.main
        }">${DateTime.fromMillis(dateStr).toFormat('DD HH:mm:ss')}</div>`;

      const toolTipWidth = 80;
      const toolTipHeight = 80;
      const toolTipMargin = 15;

      const coordinate = lineSeriesRef.current.priceToCoordinate(price);
      let shiftedCoordinate = param.point.x - 50;
      if (coordinate === null) return;

      shiftedCoordinate = Math.max(
        0,
        Math.min(
          chartContainerRef.current.clientWidth - toolTipWidth,
          shiftedCoordinate
        )
      );
      const coordinateY =
        coordinate - toolTipHeight - toolTipMargin > 0
          ? coordinate - toolTipHeight - toolTipMargin
          : Math.max(
              0,
              Math.min(
                chartContainerRef.current.clientHeight -
                  toolTipHeight -
                  toolTipMargin,
                coordinate + toolTipMargin
              )
            );
      tooltipRef.current.style.left = `${shiftedCoordinate}px`;
      tooltipRef.current.style.top = `${coordinateY}px`;
    }
  };

  const onVisibleLogicalRangeChange = (newVisibleLogicalRange) => {
    const newBarsInfo = lineSeriesRef.current.barsInLogicalRange(
      newVisibleLogicalRange
    );
    if (newBarsInfo && Math.floor(newBarsInfo.barsAfter) === 0)
      setBarsInfo(null);
    else setBarsInfo(newBarsInfo);
  };
  const debouncedOnVisibleLogicalRangeChange = useCallback(
    debounce(onVisibleLogicalRangeChange, 500, {
      leading: false,
      trailing: true,
    }),
    []
  );

  useEffect(() => {
    if (chartRef.current) chartRef.current.remove();
    chartRef.current = createChart(chartContainerRef.current, {
      leftPriceScale: { visible: true },
      rightPriceScale: { visible: true },
      layout: {
        background: { color: theme.palette.background.paper },
        textColor: theme.palette.text.main,
      },
      grid: {
        horzLines: { color: alpha(theme.palette.grey['600'], 0.15) },
        vertLines: { color: alpha(theme.palette.grey['600'], 0.15) },
      },
      //  handleScale: isAuthorized,
      //  handleScroll: isAuthorized,
      localization: {
        timeFormatter: (time) =>
          DateTime.fromMillis(time).toFormat('DD HH:mm:ss'),
      },
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
      width: chartContainerRef.current?.clientWidth,
      height: CHART_HEIGHT,
    });
    chartRef.current.timeScale().applyOptions({
      barSpacing: 10,
      borderColor: alpha(theme.palette.secondary.main, 0.2),
      fixRightEdge: true,
      rightOffset: 2,
      tickMarkFormatter: (time) => DateTime.fromMillis(time).toFormat('HH:mm'),
    });
    chartRef.current
      .timeScale()
      .subscribeVisibleLogicalRangeChange(debouncedOnVisibleLogicalRangeChange);
    chartRef.current.subscribeCrosshairMove(onCrosshairMove);
    lineSeriesRef.current = chartRef.current.addLineSeries({
      priceScaleId: 'left',
      color: theme.palette.primary.main,
      crosshairMarkerVisible: false,
      // lastValueVisible: false,
      // lastPriceAnimation: LastPriceAnimationMode.OnDataUpdate,
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
    return () => {
      chartRef.current
        .timeScale()
        .unsubscribeVisibleLogicalRangeChange(
          debouncedOnVisibleLogicalRangeChange
        );
      chartRef.current.unsubscribeCrosshairMove(onCrosshairMove);
    };
  }, []);

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

  const prevBarsInfo = usePrevious(barsInfo);
  useEffect(() => {
    if (!isFetching && barsInfo && Math.floor(barsInfo.barsBefore) < 0) {
      const diff = prevBarsInfo
        ? Math.floor(prevBarsInfo.barsBefore) - Math.floor(barsInfo.barsBefore)
        : 0;
      if (!prevBarsInfo || Math.abs(diff) > 10) {
        const newEndTime = DateTime.fromMillis(barsInfo.from).minus({
          seconds: 1,
        });
        const newStartTime = newEndTime.minus({
          hours: Math.abs(Math.floor(barsInfo.barsBefore)) * 50,
        });
        setEndFundingTime(newEndTime.toFormat(DATE_FORMAT_API_QUERY));
        setStartFundingTime(
          newStartTime.startOf('hour').toFormat(DATE_FORMAT_API_QUERY)
        );
      }
    }
  }, [barsInfo, isFetching]);

  useEffect(() => {
    const isDark = theme.palette.mode === 'dark';
    chartRef.current.applyOptions({
      layout: {
        background: { color: theme.palette.background.paper },
        textColor: theme.palette.text.main,
      },
      crosshair: {
        vertLine: {
          labelBackgroundColor: theme.palette.grey[isDark ? '800' : '100'],
        },
        horzLine: {
          labelBackgroundColor: theme.palette.grey[isDark ? '800' : '100'],
        },
      },
    });
  }, [theme.palette.mode]);

  useEffect(() => {
    chartRef.current.applyOptions({ layout: { fontSize: isMobile ? 8 : 11 } });
  }, [isMobile, i18n.language]);

  useEffect(() => {
    lineSeriesRef.current.applyOptions({ title: t('Price') });
  }, [i18n.language]);

  return (
    <Card onClick={(e) => e.stopPropagation()} sx={{ borderRadius: 0 }}>
      <Box sx={{ bgcolor: 'background.paper' }}>
        {isFetching && <LinearProgress />}
        <Box
          ref={chartContainerRef}
          onClick={(e) => e.stopPropagation()}
          sx={{ position: 'relative' }}
        >
          {barsInfo?.barsAfter > 100 && (
            <IconButton
              color="dark"
              size="small"
              onClick={() => {
                chartRef.current.timeScale().scrollToPosition(0, true);
                setBarsInfo(null);
                setTimeout(
                  () =>
                    chartRef.current
                      .timeScale()
                      .applyOptions({ rightOffset: 2, fixRightEdge: true }),
                  0
                );
              }}
              sx={{
                bgcolor: 'accent.main',
                position: 'absolute',
                bottom: 10,
                right: 10,
                zIndex: 3,
                ':hover': { bgcolor: 'accent.main', opacity: 0.7 },
              }}
            >
              <ArrowForwardIosIcon />
            </IconButton>
          )}
          <Card
            ref={tooltipRef}
            sx={{
              display: 'none',
              position: 'absolute',
              width: 120,
              height: 120,
              zIndex: 1000,
              border: 0.5,
              borderColor: 'secondary.main',
              p: 1,
            }}
          />
        </Box>
      </Box>
    </Card>
  );
}
