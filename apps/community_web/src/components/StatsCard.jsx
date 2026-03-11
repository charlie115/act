import React, { memo } from 'react';
import { Box, Paper, Skeleton, Stack, Typography } from '@mui/material';
import { useTheme, alpha, keyframes } from '@mui/material/styles';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingFlatIcon from '@mui/icons-material/TrendingFlat';
import Sparkline from './Sparkline';

// Entrance animation
const fadeInUp = keyframes`
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

// Subtle pulse for the trend indicator
const subtlePulse = keyframes`
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
`;

/**
 * StatsCard - Premium stat display card for trading dashboards
 *
 * A refined, glassmorphic stat card with trend indicators, animated values,
 * and optional sparkline integration. Designed for cryptocurrency trading interfaces.
 *
 * @param {Object} props
 * @param {string} props.title - Card title/label
 * @param {string|number} props.value - Main value to display
 * @param {number} [props.change] - Change percentage (positive or negative)
 * @param {React.ReactNode} [props.icon] - Icon to display
 * @param {'up'|'down'|'neutral'} [props.trend='neutral'] - Trend direction
 * @param {boolean} [props.loading=false] - Loading state
 * @param {number[]} [props.sparklineData] - Optional sparkline data array
 * @param {number} [props.animationDelay=0] - Animation delay in seconds for staggered entrance
 * @param {Object} [props.sx] - Additional MUI sx styles
 */
const StatsCard = memo(({
  title,
  value,
  change,
  icon,
  trend = 'neutral',
  loading = false,
  sparklineData,
  animationDelay = 0,
  sx,
}) => {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  // Get trend-based colors
  const getTrendColor = () => {
    if (trend === 'up') return theme.palette.success.main;
    if (trend === 'down') return theme.palette.error.main;
    return theme.palette.text.secondary;
  };

  // Get trend-based gradient overlay
  const getTrendGradient = () => {
    if (trend === 'up') {
      return isDark
        ? `linear-gradient(135deg, ${alpha(theme.palette.success.main, 0.06)} 0%, transparent 60%)`
        : `linear-gradient(135deg, ${alpha(theme.palette.success.main, 0.04)} 0%, transparent 60%)`;
    }
    if (trend === 'down') {
      return isDark
        ? `linear-gradient(135deg, ${alpha(theme.palette.error.main, 0.06)} 0%, transparent 60%)`
        : `linear-gradient(135deg, ${alpha(theme.palette.error.main, 0.04)} 0%, transparent 60%)`;
    }
    return 'none';
  };

  // Get trend icon props
  const trendIconProps = {
    sx: {
      fontSize: '0.875rem',
      color: getTrendColor(),
      animation: trend !== 'neutral' ? `${subtlePulse} 2s ease-in-out infinite` : 'none',
    },
  };

  // Render the appropriate trend icon
  const renderTrendIcon = () => {
    if (trend === 'up') return <TrendingUpIcon {...trendIconProps} />;
    if (trend === 'down') return <TrendingDownIcon {...trendIconProps} />;
    return <TrendingFlatIcon {...trendIconProps} />;
  };

  // Format change percentage
  const formatChange = (val) => {
    if (val === undefined || val === null) return null;
    const sign = val >= 0 ? '+' : '';
    return `${sign}${val.toFixed(2)}%`;
  };

  if (loading) {
    return (
      <Paper
        elevation={0}
        sx={{
          p: 2.5,
          borderRadius: 2,
          border: `1px solid ${alpha(theme.palette.divider, 0.08)}`,
          backgroundColor: theme.palette.background.paper,
          ...sx,
        }}
      >
        <Stack spacing={1.5}>
          <Skeleton variant="text" width="40%" height={20} />
          <Skeleton variant="text" width="60%" height={36} />
          <Skeleton variant="text" width="30%" height={18} />
        </Stack>
      </Paper>
    );
  }

  return (
    <Paper
      elevation={0}
      sx={{
        p: 2.5,
        borderRadius: 2,
        position: 'relative',
        overflow: 'hidden',
        // Glassmorphism effect
        backgroundColor: isDark
          ? alpha(theme.palette.background.paper, 0.7)
          : alpha(theme.palette.background.paper, 0.9),
        backdropFilter: 'blur(12px) saturate(180%)',
        border: `1px solid ${alpha(theme.palette.divider, isDark ? 0.08 : 0.12)}`,
        // Entrance animation
        opacity: 0,
        animation: `${fadeInUp} 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards`,
        animationDelay: `${animationDelay}s`,
        // Transition for hover
        transition: theme.transitions.create(['border-color', 'box-shadow', 'transform'], {
          duration: theme.transitions.duration.short,
        }),
        '&:hover': {
          borderColor: alpha(theme.palette.primary.main, 0.15),
          boxShadow: isDark
            ? `0 8px 24px ${alpha(theme.palette.common.black, 0.3)}`
            : `0 8px 24px ${alpha(theme.palette.common.black, 0.08)}`,
          transform: 'translateY(-2px)',
        },
        // Trend-based gradient overlay
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: getTrendGradient(),
          pointerEvents: 'none',
        },
        // Top highlight for depth
        '&::after': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: '10%',
          right: '10%',
          height: '1px',
          background: isDark
            ? 'linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent)'
            : 'linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent)',
          pointerEvents: 'none',
        },
        ...sx,
      }}
    >
      <Stack spacing={1.5} sx={{ position: 'relative', zIndex: 1 }}>
        {/* Header: Title and Icon */}
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Typography
            variant="caption"
            sx={{
              color: 'text.secondary',
              fontWeight: 500,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              fontSize: '0.6875rem',
            }}
          >
            {title}
          </Typography>
          {icon && (
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 32,
                height: 32,
                borderRadius: 1,
                backgroundColor: alpha(theme.palette.primary.main, isDark ? 0.12 : 0.08),
                color: theme.palette.primary.main,
                '& svg': {
                  fontSize: '1.125rem',
                },
              }}
            >
              {icon}
            </Box>
          )}
        </Stack>

        {/* Main Value */}
        <Typography
          variant="h5"
          sx={{
            fontFamily: '"JetBrains Mono", "SF Mono", "Fira Code", monospace',
            fontFeatureSettings: '"tnum" 1',
            fontWeight: 700,
            fontSize: { xs: '1.25rem', sm: '1.5rem' },
            letterSpacing: '-0.02em',
            color: 'text.primary',
            lineHeight: 1.2,
          }}
        >
          {value}
        </Typography>

        {/* Change and Sparkline Row */}
        <Stack direction="row" alignItems="center" justifyContent="space-between" spacing={2}>
          {/* Change Percentage with Trend */}
          {change !== undefined && (
            <Stack direction="row" alignItems="center" spacing={0.5}>
              {renderTrendIcon()}
              <Typography
                variant="body2"
                sx={{
                  fontFamily: '"JetBrains Mono", "SF Mono", monospace',
                  fontFeatureSettings: '"tnum" 1',
                  fontWeight: 600,
                  fontSize: '0.75rem',
                  color: getTrendColor(),
                }}
              >
                {formatChange(change)}
              </Typography>
            </Stack>
          )}

          {/* Sparkline */}
          {sparklineData && sparklineData.length > 1 && (
            <Box sx={{ flexShrink: 0 }}>
              <Sparkline
                data={sparklineData}
                width={64}
                height={24}
                animate={false}
                strokeWidth={1.5}
              />
            </Box>
          )}
        </Stack>
      </Stack>
    </Paper>
  );
});

export default StatsCard;
