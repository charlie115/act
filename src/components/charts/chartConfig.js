import { alpha } from '@mui/material/styles';

// Modern chart color palette
export const CHART_COLORS = {
  primary: '#007cff',
  success: '#25C196',
  error: '#ff0d45',
  warning: '#faa12d',
  info: '#00bbff',
  secondary: '#64748b',
  
  // Gradient colors
  gradients: {
    primary: ['#007cff', '#0066d9'],
    success: ['#51d2ad', '#25C196'],
    error: ['#ff0d45', '#d32f2f'],
    warning: ['#faa12d', '#f57c00'],
    info: ['#00bbff', '#0072b3'],
  },
  
  // Chart specific colors
  candlestick: {
    up: '#25C196',
    down: '#ff0d45',
  },
  volume: {
    up: 'rgba(37, 193, 150, 0.5)',
    down: 'rgba(255, 13, 69, 0.5)',
  },
};

// Base chart options for Lightweight Charts
export const getBaseChartOptions = (theme) => ({
  layout: {
    background: {
      type: 'solid',
      color: 'transparent',
    },
    textColor: theme.palette.text.primary,
    fontFamily: theme.typography.fontFamily,
    fontSize: 12,
  },
  grid: {
    vertLines: {
      color: alpha(theme.palette.divider, 0.3),
      style: 1,
    },
    horzLines: {
      color: alpha(theme.palette.divider, 0.3),
      style: 1,
    },
  },
  crosshair: {
    mode: 1, // Normal mode
    vertLine: {
      color: alpha(theme.palette.primary.main, 0.5),
      width: 1,
      style: 2, // Dashed
      labelBackgroundColor: theme.palette.primary.main,
    },
    horzLine: {
      color: alpha(theme.palette.primary.main, 0.5),
      width: 1,
      style: 2, // Dashed
      labelBackgroundColor: theme.palette.primary.main,
    },
  },
  handleScroll: {
    mouseWheel: true,
    pressedMouseMove: true,
    horzTouchDrag: true,
    vertTouchDrag: false,
  },
  handleScale: {
    axisPressedMouseMove: true,
    mouseWheel: true,
    pinch: true,
  },
});

// Time scale options
export const getTimeScaleOptions = (theme) => ({
  rightOffset: 5,
  barSpacing: 10,
  minBarSpacing: 3,
  fixLeftEdge: false,
  fixRightEdge: false,
  lockVisibleTimeRangeOnResize: true,
  rightBarStaysOnScroll: true,
  borderColor: theme.palette.divider,
  visible: true,
  timeVisible: true,
  secondsVisible: false,
  tickMarkFormatter: (time, tickMarkType, locale) => {
    const date = new Date(time * 1000);
    switch (tickMarkType) {
      case 0: // Year
        return date.getFullYear();
      case 1: // Month
        return date.toLocaleDateString(locale, { month: 'short' });
      case 2: // DayOfMonth
        return date.getDate();
      case 3: // Time
        return date.toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' });
      case 4: // TimeWithSeconds
        return date.toLocaleTimeString(locale);
      default:
        return '';
    }
  },
});

// Price scale options
export const getPriceScaleOptions = (theme) => ({
  borderColor: theme.palette.divider,
  visible: true,
  autoScale: true,
  mode: 0, // Normal mode
  invertScale: false,
  alignLabels: true,
  scaleMargins: {
    top: 0.1,
    bottom: 0.1,
  },
  drawTicks: false,
});

// Candlestick series options
export const getCandlestickOptions = () => ({
  upColor: CHART_COLORS.candlestick.up,
  downColor: CHART_COLORS.candlestick.down,
  borderUpColor: CHART_COLORS.candlestick.up,
  borderDownColor: CHART_COLORS.candlestick.down,
  wickUpColor: CHART_COLORS.candlestick.up,
  wickDownColor: CHART_COLORS.candlestick.down,
  borderVisible: true,
  wickVisible: true,
});

// Line series options
export const getLineSeriesOptions = (theme, color = CHART_COLORS.primary) => ({
  color,
  lineWidth: 2,
  lineStyle: 0, // Solid
  lineType: 0, // Simple
  crosshairMarkerVisible: true,
  crosshairMarkerRadius: 4,
  crosshairMarkerBorderColor: color,
  crosshairMarkerBackgroundColor: theme.palette.background.paper,
  lastValueVisible: true,
  priceLineVisible: true,
  priceLineWidth: 1,
  priceLineColor: alpha(color, 0.5),
  priceLineStyle: 2, // Dashed
});

// Area series options
export const getAreaSeriesOptions = (theme, color = CHART_COLORS.primary) => ({
  topColor: alpha(color, 0.5),
  bottomColor: alpha(color, 0.05),
  lineColor: color,
  lineWidth: 2,
  lineStyle: 0, // Solid
  lineType: 0, // Simple
  crosshairMarkerVisible: true,
  crosshairMarkerRadius: 4,
  crosshairMarkerBorderColor: color,
  crosshairMarkerBackgroundColor: theme.palette.background.paper,
  lastValueVisible: true,
  priceLineVisible: true,
  priceLineWidth: 1,
  priceLineColor: alpha(color, 0.5),
  priceLineStyle: 2, // Dashed
});

// Histogram (volume) series options
export const getHistogramOptions = () => ({
  color: CHART_COLORS.volume.up,
  priceFormat: {
    type: 'volume',
  },
  overlay: true,
  scaleMargins: {
    top: 0.8,
    bottom: 0,
  },
});

// Tooltip options
export const getTooltipOptions = (theme) => ({
  backgroundColor: alpha(theme.palette.background.paper, 0.95),
  borderColor: theme.palette.divider,
  borderRadius: theme.shape.borderRadius / 2,
  color: theme.palette.text.primary,
  fontFamily: theme.typography.fontFamily,
  fontSize: theme.typography.caption.fontSize,
  padding: theme.spacing(1),
});

// Chart.js options
export const getChartJsOptions = (theme, options = {}) => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false,
  },
  plugins: {
    legend: {
      display: true,
      position: 'top',
      align: 'end',
      labels: {
        boxWidth: 12,
        boxHeight: 12,
        padding: 16,
        usePointStyle: true,
        font: {
          size: 12,
          family: theme.typography.fontFamily,
        },
        color: theme.palette.text.secondary,
      },
    },
    tooltip: {
      enabled: true,
      backgroundColor: alpha(theme.palette.background.paper, 0.95),
      titleColor: theme.palette.text.primary,
      bodyColor: theme.palette.text.secondary,
      borderColor: theme.palette.divider,
      borderWidth: 1,
      padding: 12,
      cornerRadius: theme.shape.borderRadius / 2,
      displayColors: true,
      titleFont: {
        size: 13,
        weight: 600,
      },
      bodyFont: {
        size: 12,
      },
    },
  },
  scales: {
    x: {
      grid: {
        display: false,
        drawBorder: false,
      },
      ticks: {
        color: theme.palette.text.secondary,
        font: {
          size: 11,
        },
      },
    },
    y: {
      grid: {
        color: alpha(theme.palette.divider, 0.3),
        drawBorder: false,
      },
      ticks: {
        color: theme.palette.text.secondary,
        font: {
          size: 11,
        },
      },
    },
  },
  ...options,
});