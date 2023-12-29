import React, {
  forwardRef,
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react';

import { useNavigate } from 'react-router-dom';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import IconButton from '@mui/material/IconButton';
import LinearProgress from '@mui/material/LinearProgress';

import ArrowForwardIosIcon from '@mui/icons-material/ArrowForwardIos';

import { alpha, useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

import { createChart, CrosshairMode } from 'lightweight-charts';

import { useTranslation } from 'react-i18next';

import { usePrevious } from '@uidotdev/usehooks';

import { DateTime } from 'luxon';

import debounce from 'lodash/debounce';

const CHART_HEIGHT = 250;

const LightWeightBaseChart = forwardRef(
  (
    {
      baseSeriesRef,
      chartOptions = {},
      timeScaleOptions = {},
      tooltipOptions = {},
      dependencies = [],
      interval,
      isLoading,
      isUnauthorized,
      onBarsInfoChanged,
      onReady,
    },
    ref
  ) => {
    const navigate = useNavigate();

    const containerRef = useRef();
    const tooltipRef = useRef();

    const { t } = useTranslation();

    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('md'));

    const [barsInfo, setBarsInfo] = useState(null);

    const onVisibleLogicalRangeChange = (newVisibleLogicalRange) => {
      const newBarsInfo = baseSeriesRef.current.barsInLogicalRange(
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

    const onCrosshairMove = (param) => {
      if (!tooltipOptions.enabled) return;
      if (
        param.point === undefined ||
        !param.time ||
        param.point.x < 0 ||
        param.point.x > containerRef.current.clientWidth ||
        param.point.y < 0 ||
        param.point.y > containerRef.current.clientHeight
      ) {
        // tooltipRef.current.style.display = 'none';
      } else {
        const dateStr = param.time;
        tooltipRef.current.style.display = 'block';
        const currentData = param.seriesData.get(baseSeriesRef.current);
        const price =
          currentData.value !== undefined
            ? currentData.value
            : currentData.close;
        tooltipRef.current.innerHTML = tooltipOptions.getInnerHTML
          ? tooltipOptions.getInnerHTML(price, dateStr)
          : '';

        const toolTipWidth = 80;
        const toolTipHeight = 80;
        const toolTipMargin = 15;

        const coordinate = baseSeriesRef.current.priceToCoordinate(price);
        let shiftedCoordinate = param.point.x - 50;
        if (coordinate === null) return;

        shiftedCoordinate = Math.max(
          0,
          Math.min(
            containerRef.current.clientWidth - toolTipWidth,
            shiftedCoordinate
          )
        );
        const coordinateY =
          coordinate - toolTipHeight - toolTipMargin > 0
            ? coordinate - toolTipHeight - toolTipMargin
            : Math.max(
                0,
                Math.min(
                  containerRef.current.clientHeight -
                    toolTipHeight -
                    toolTipMargin,
                  coordinate + toolTipMargin
                )
              );
        tooltipRef.current.style.left = `${shiftedCoordinate}px`;
        tooltipRef.current.style.top = `${coordinateY}px`;
      }
    };

    useEffect(() => {
      if (ref.current) ref.current.remove();
      ref.current = createChart(containerRef.current, {
        leftPriceScale: { visible: true },
        layout: {
          background: { color: theme.palette.background.paper },
          textColor: theme.palette.text.main,
        },
        grid: {
          horzLines: { color: alpha(theme.palette.grey['600'], 0.15) },
          vertLines: { color: alpha(theme.palette.grey['600'], 0.15) },
        },
        localization: {
          timeFormatter: (time) =>
            DateTime.fromMillis(time).toFormat('DD HH:mm:ss'),
        },
        crosshair: { mode: CrosshairMode.Normal },
        width: containerRef.current?.clientWidth,
        height: CHART_HEIGHT,
      });
      ref.current.priceScale('left').applyOptions({
        borderColor: alpha(theme.palette.secondary.main, 0.2),
      });
      ref.current.priceScale('right').applyOptions({
        borderColor: alpha(theme.palette.secondary.main, 0.2),
      });
      ref.current.timeScale().applyOptions({
        barSpacing: 10,
        borderColor: alpha(theme.palette.secondary.main, 0.2),
        fixRightEdge: true,
        rightOffset: 2,
        tickMarkFormatter: (time) =>
          DateTime.fromMillis(time).toFormat('HH:mm'),
        ...timeScaleOptions,
      });
      ref.current
        .timeScale()
        .subscribeVisibleLogicalRangeChange(
          debouncedOnVisibleLogicalRangeChange
        );
      ref.current.subscribeCrosshairMove(onCrosshairMove);

      if (onReady) onReady(ref);

      return () => {
        ref.current
          .timeScale()
          .unsubscribeVisibleLogicalRangeChange(
            debouncedOnVisibleLogicalRangeChange
          );
        ref.current.unsubscribeCrosshairMove(onCrosshairMove);
      };
    }, [...dependencies]);

    useEffect(() => {
      ref.current.applyOptions(chartOptions);
    }, [chartOptions]);

    useEffect(() => {
      if (isUnauthorized) {
        const canvas = document.querySelector(
          '.tv-lightweight-charts td:nth-child(2) canvas:nth-child(2)'
        );
        canvas.style.backdropFilter = 'blur(10px)';
        canvas.style['-webkit-backdrop-filter'] = 'blur(10px)';
        canvas.style.pointerEvents = 'none';
      }
    }, [isUnauthorized]);

    useEffect(() => {
      const isDark = theme.palette.mode === 'dark';
      ref.current.applyOptions({
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
      ref.current.applyOptions({
        layout: { fontSize: isMobile ? 8 : 11 },
      });
    }, [isMobile]);

    const prevBarsInfo = usePrevious(barsInfo);
    useEffect(() => {
      if (barsInfo && Math.floor(barsInfo.barsBefore) < 0) {
        const diff = prevBarsInfo
          ? Math.floor(prevBarsInfo.barsBefore) -
            Math.floor(barsInfo.barsBefore)
          : 0;
        if (!prevBarsInfo || Math.abs(diff) > 10) {
          const { quantity, unit } = interval;
          const endTime = DateTime.fromMillis(barsInfo.from).minus({
            [unit]: 1,
          });
          const startTime = endTime.minus({
            [unit]: quantity * Math.abs(Math.floor(barsInfo.barsBefore)) * 50,
          });
          onBarsInfoChanged({ start: startTime, end: endTime });
        }
      }
    }, [barsInfo, interval]);

    return (
      <>
        {isLoading && <LinearProgress />}
        <Box
          ref={containerRef}
          sx={{ position: 'relative', pt: 2 }}
          onClick={(e) => e.stopPropagation()}
          onMouseLeave={() => {
            if (tooltipRef.current) tooltipRef.current.style.display = 'none';
          }}
        >
          {isUnauthorized && (
            <Button
              color="error"
              size="large"
              onClick={() => navigate('/login')}
              sx={{
                position: 'absolute',
                top: '35%',
                left: '50%',
                transform: 'translateX(-50%)',
                zIndex: 3,
              }}
            >
              {t('Login to view data')}
            </Button>
          )}
          {barsInfo?.barsAfter > 100 && (
            <IconButton
              color="dark"
              size="small"
              onClick={() => {
                ref.current.timeScale().scrollToPosition(0, true);
                setBarsInfo(null);
                setTimeout(
                  () =>
                    ref.current
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
      </>
    );
  }
);

export default LightWeightBaseChart;
