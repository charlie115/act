import React, { memo, useMemo, useId } from 'react';
import { useTheme, alpha, keyframes } from '@mui/material/styles';
import { Box, Tooltip } from '@mui/material';

// Draw animation keyframe
const drawLine = keyframes`
  from {
    stroke-dashoffset: var(--path-length);
  }
  to {
    stroke-dashoffset: 0;
  }
`;

// Fade in animation for the gradient fill
const fadeIn = keyframes`
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
`;

/**
 * Generate smooth bezier curve path from data points
 * Uses Catmull-Rom to Bezier conversion for natural curves
 */
const generateSmoothPath = (points, width, height, padding = 2) => {
  if (!points || points.length < 2) return '';

  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;

  // Normalize points to SVG coordinates
  const normalized = points.map((val, i) => ({
    x: padding + (i / (points.length - 1)) * (width - padding * 2),
    y: padding + (1 - (val - min) / range) * (height - padding * 2),
  }));

  // Generate smooth curve using Catmull-Rom spline
  const catmullRomToBezier = (p0, p1, p2, p3, tension = 0.5) => {
    const cp1x = p1.x + (p2.x - p0.x) * tension / 3;
    const cp1y = p1.y + (p2.y - p0.y) * tension / 3;
    const cp2x = p2.x - (p3.x - p1.x) * tension / 3;
    const cp2y = p2.y - (p3.y - p1.y) * tension / 3;
    return `C ${cp1x},${cp1y} ${cp2x},${cp2y} ${p2.x},${p2.y}`;
  };

  let path = `M ${normalized[0].x},${normalized[0].y}`;

  for (let i = 0; i < normalized.length - 1; i += 1) {
    const p0 = normalized[i - 1] || normalized[0];
    const p1 = normalized[i];
    const p2 = normalized[i + 1];
    const p3 = normalized[i + 2] || normalized[normalized.length - 1];
    path += ` ${catmullRomToBezier(p0, p1, p2, p3)}`;
  }

  return path;
};

/**
 * Generate closed path for gradient fill area
 */
const generateAreaPath = (points, width, height, padding = 2) => {
  const linePath = generateSmoothPath(points, width, height, padding);
  if (!linePath) return '';

  const lastX = padding + (width - padding * 2);
  const firstX = padding;
  const bottomY = height - padding;

  return `${linePath} L ${lastX},${bottomY} L ${firstX},${bottomY} Z`;
};

/**
 * Sparkline - Mini chart for displaying price trends
 *
 * A refined, data-focused sparkline component for trading applications.
 * Features smooth bezier curves, gradient fills, and drawing animation.
 *
 * @param {Object} props
 * @param {number[]} props.data - Array of numeric values representing price/data history
 * @param {number} [props.width=60] - Width of the sparkline in pixels
 * @param {number} [props.height=24] - Height of the sparkline in pixels
 * @param {boolean} [props.showTooltip=false] - Whether to show tooltip on hover
 * @param {string|number} [props.tooltipValue] - Custom tooltip value to display
 * @param {boolean} [props.animate=true] - Whether to animate on mount
 * @param {number} [props.strokeWidth=1.5] - Stroke width of the line
 * @param {string} [props.className] - Additional className
 * @param {Object} [props.sx] - MUI sx prop for additional styling
 */
const Sparkline = memo(({
  data = [],
  width = 60,
  height = 24,
  showTooltip = false,
  tooltipValue,
  animate = true,
  strokeWidth = 1.5,
  className,
  sx,
}) => {
  const theme = useTheme();
  const uniqueId = useId();
  const gradientId = `sparkline-gradient-${uniqueId}`;
  const areaGradientId = `sparkline-area-${uniqueId}`;

  // Determine trend direction
  const trend = useMemo(() => {
    if (!data || data.length < 2) return 'neutral';
    const first = data[0];
    const last = data[data.length - 1];
    if (last > first) return 'up';
    if (last < first) return 'down';
    return 'neutral';
  }, [data]);

  // Get colors based on trend
  const colors = useMemo(() => {
    const trendColors = {
      up: {
        stroke: '#25C196',
        gradientStart: alpha('#25C196', 0.4),
        gradientEnd: alpha('#25C196', 0),
      },
      down: {
        stroke: '#ff0d45',
        gradientStart: alpha('#ff0d45', 0.4),
        gradientEnd: alpha('#ff0d45', 0),
      },
      neutral: {
        stroke: theme.palette.text.secondary,
        gradientStart: alpha(theme.palette.text.secondary, 0.2),
        gradientEnd: alpha(theme.palette.text.secondary, 0),
      },
    };
    return trendColors[trend];
  }, [trend, theme.palette.text.secondary]);

  // Generate paths
  const { linePath, areaPath, pathLength } = useMemo(() => {
    const line = generateSmoothPath(data, width, height);
    const area = generateAreaPath(data, width, height);

    // Estimate path length for animation
    const estimated = data.length > 1 ? width * 1.5 : 0;

    return { linePath: line, areaPath: area, pathLength: estimated };
  }, [data, width, height]);

  // Handle empty/insufficient data
  if (!data || data.length < 2) {
    return (
      <Box
        component="span"
        sx={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width,
          height,
          color: theme.palette.text.disabled,
          fontSize: '0.625rem',
          fontFamily: theme.typography.fontFamilyMono,
          ...sx,
        }}
        className={className}
      >
        —
      </Box>
    );
  }

  // Calculate end point Y position
  const endPointY = (() => {
    if (!data || data.length < 2) return height / 2;
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    return 2 + (1 - (data[data.length - 1] - min) / range) * (height - 4);
  })();

  const sparklineContent = (
    <Box
      component="span"
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        cursor: showTooltip ? 'pointer' : 'default',
        ...sx,
      }}
      className={className}
    >
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        style={{
          overflow: 'visible',
          display: 'block',
        }}
      >
        <defs>
          {/* Line gradient for slight shimmer effect */}
          <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={colors.stroke} stopOpacity="0.8" />
            <stop offset="50%" stopColor={colors.stroke} stopOpacity="1" />
            <stop offset="100%" stopColor={colors.stroke} stopOpacity="0.8" />
          </linearGradient>

          {/* Area fill gradient (vertical fade) */}
          <linearGradient id={areaGradientId} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor={colors.gradientStart} />
            <stop offset="100%" stopColor={colors.gradientEnd} />
          </linearGradient>
        </defs>

        {/* Gradient fill area */}
        <path
          d={areaPath}
          fill={`url(#${areaGradientId})`}
          style={animate ? {
            animation: `${fadeIn} 0.6s ease-out 0.3s forwards`,
            opacity: 0,
          } : undefined}
        />

        {/* Main line with draw animation */}
        <path
          d={linePath}
          fill="none"
          stroke={`url(#${gradientId})`}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{
            '--path-length': pathLength,
            ...(animate && {
              strokeDasharray: pathLength,
              strokeDashoffset: pathLength,
              animation: `${drawLine} 0.8s cubic-bezier(0.65, 0, 0.35, 1) forwards`,
            }),
          }}
        />

        {/* End point dot */}
        <circle
          cx={width - 2}
          cy={endPointY}
          r={2}
          fill={colors.stroke}
          style={animate ? {
            opacity: 0,
            animation: `${fadeIn} 0.3s ease-out 0.7s forwards`,
          } : undefined}
        />
      </svg>
    </Box>
  );

  if (showTooltip && tooltipValue !== undefined) {
    return (
      <Tooltip
        title={
          <Box
            sx={{
              fontFamily: theme.typography.fontFamilyMono,
              fontSize: '0.75rem',
              fontWeight: 600,
            }}
          >
            {tooltipValue}
          </Box>
        }
        arrow
        placement="top"
      >
        {sparklineContent}
      </Tooltip>
    );
  }

  return sparklineContent;
});

export default Sparkline;
