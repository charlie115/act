import React, { memo } from 'react';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import { alpha, useTheme } from '@mui/material/styles';
import formatIntlNumber from 'utils/formatIntlNumber';
import formatShortNumber from 'utils/formatShortNumber';
import isUndefined from 'lodash/isUndefined';

// Import original renderers
import renderNameCellOriginal from './renderNameCell';
import renderStarCellOriginal from './renderStarCell';
import renderWalletStatusCellOriginal from './renderWalletStatusCell';

/**
 * Get heat map background color based on value intensity
 * @param {number} value - The value to colorize
 * @param {object} theme - MUI theme object
 * @param {number} threshold - Max value for full intensity (default 5)
 * @returns {string} Background color
 */
const getHeatMapColor = (value, theme, threshold = 5) => {
  if (value === 0 || isUndefined(value)) return 'transparent';

  const isDark = theme.palette.mode === 'dark';
  const intensity = Math.min(Math.abs(value) / threshold, 1);
  const index = Math.min(Math.floor(intensity * 5), 4);

  const positiveColors = isDark
    ? ['rgba(37, 193, 150, 0.08)', 'rgba(37, 193, 150, 0.15)', 'rgba(37, 193, 150, 0.22)', 'rgba(37, 193, 150, 0.3)', 'rgba(37, 193, 150, 0.4)']
    : ['#e8f9f4', '#c3f0e3', '#9de6d1', '#77dcbf', '#51d2ad'];

  const negativeColors = isDark
    ? ['rgba(255, 13, 69, 0.08)', 'rgba(255, 13, 69, 0.15)', 'rgba(255, 13, 69, 0.22)', 'rgba(255, 13, 69, 0.3)', 'rgba(255, 13, 69, 0.4)']
    : ['#ffebee', '#ffcdd2', '#ef9a9a', '#ef5350', '#ff0d45'];

  return value > 0 ? positiveColors[index] : negativeColors[index];
};

/**
 * Get text color based on value (positive/negative/neutral)
 */
const getValueColor = (value) => {
  if (value > 0) return 'success.main';
  if (value < 0) return 'error.main';
  return 'text.primary';
};

/**
 * Common styles for monospace numeric display
 */
const monoStyles = {
  fontFamily: '"JetBrains Mono", "SF Mono", "Fira Code", monospace',
  fontFeatureSettings: '"tnum" 1',
  letterSpacing: '-0.01em',
};

/**
 * Pill/badge container for values
 */
function PillContainer({ children, color, sx, ...props }) {
  return (
    <Box
      component="span"
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        px: 0.75,
        py: 0.25,
        borderRadius: 1,
        backgroundColor: color,
        transition: 'background-color 0.2s ease',
        ...sx,
      }}
      {...props}
    >
      {children}
    </Box>
  );
}

// Memoized premium cell renderer with heat map background
export const renderPremiumCell = memo(({ cell, row: { original }, table }) => {
  const theme = useTheme();
  const value = cell.getValue();

  if (isUndefined(value)) return '...';

  const { isMobile, isTetherPriceView } = table.options.meta;
  const heatColor = getHeatMapColor(value, theme, 3);

  return isTetherPriceView ? (
    <PillContainer color={heatColor}>
      <Box
        component="span"
        sx={{
          ...monoStyles,
          fontSize: { xs: '0.5rem', sm: '0.75rem' },
          fontWeight: 600,
          color: getValueColor(value),
        }}
      >
        {formatIntlNumber(original.dollar * (1 + value * 0.01), isMobile ? 1 : 2)}
      </Box>
    </PillContainer>
  ) : (
    <PillContainer color={heatColor}>
      <Box
        component="span"
        sx={{
          ...monoStyles,
          fontSize: { xs: '0.5rem', sm: '0.75rem' },
          fontWeight: 600,
          color: getValueColor(value),
        }}
      >
        {value > 0 && '+'}
        {formatIntlNumber(value, isMobile ? 2 : 3)}
        <Box
          component="span"
          sx={{
            ml: 0.25,
            fontSize: { xs: '0.4375rem', sm: '0.625rem' },
            color: 'text.secondary',
            fontWeight: 400,
          }}
        >
          %
        </Box>
      </Box>
    </PillContainer>
  );
}, (prevProps, nextProps) => (
  prevProps.cell.getValue() === nextProps.cell.getValue() &&
  prevProps.row.original.dollar === nextProps.row.original.dollar &&
  prevProps.table.options.meta.isMobile === nextProps.table.options.meta.isMobile &&
  prevProps.table.options.meta.isTetherPriceView === nextProps.table.options.meta.isTetherPriceView
));

// Memoized price cell renderer with trend indicator
export const renderPriceCell = memo(({ cell, row: { original }, table }) => {
  const theme = useTheme();
  const value = cell.getValue();
  const { isMobile: _isMobile } = table.options.meta;

  if (isUndefined(value)) return '...';

  const changePercent = original.scr || 0;
  const isPositive = changePercent >= 0;

  return (
    <Box>
      {/* Change percentage badge + Target market price on same row */}
      <Stack direction="row" alignItems="center" spacing={{ xs: 0.5, sm: 0.75 }} sx={{ justifyContent: { xs: 'flex-start', sm: 'flex-end' } }}>
        <Box
          component="span"
          sx={{
            ...monoStyles,
            display: 'inline-flex',
            alignItems: 'center',
            px: { xs: 0.375, sm: 0.5 },
            py: 0.125,
            borderRadius: 0.5,
            fontSize: { xs: '0.4375rem', sm: '0.6875rem' },
            fontWeight: 700,
            color: isPositive ? 'success.main' : 'error.main',
            backgroundColor: isPositive
              ? alpha(theme.palette.success.main, 0.1)
              : alpha(theme.palette.error.main, 0.1),
          }}
        >
          {isPositive ? '+' : ''}{changePercent?.toFixed(2)}%
        </Box>
        <Box
          component="span"
          sx={{
            ...monoStyles,
            fontSize: { xs: '0.5rem', sm: '0.75rem' },
            fontWeight: 600,
            color: 'text.primary',
          }}
        >
          {formatIntlNumber(value, 1)}
        </Box>
      </Stack>
      {/* Origin market price (aligned with target price on right) */}
      <Box
        component="div"
        sx={{
          ...monoStyles,
          fontSize: { xs: '0.4375rem', sm: '0.625rem' },
          fontWeight: 400,
          color: 'text.secondary',
          textAlign: { xs: 'left', sm: 'right' },
          mt: 0.25,
        }}
      >
        {formatIntlNumber(original.converted_tp, 1)}
      </Box>
    </Box>
  );
}, (prevProps, nextProps) => (
  prevProps.cell.getValue() === nextProps.cell.getValue() &&
  prevProps.row.original.c24h === nextProps.row.original.c24h &&
  prevProps.row.original.scr === nextProps.row.original.scr &&
  prevProps.row.original.converted_tp === nextProps.row.original.converted_tp &&
  prevProps.table.options.meta.isMobile === nextProps.table.options.meta.isMobile
));

// Memoized spread cell renderer with heat map
export const renderSpreadCell = memo(({ cell, table }) => {
  const theme = useTheme();
  const value = cell.getValue();
  const { isMobile: _isMobile } = table.options.meta;

  if (isUndefined(value) || value === '') return '...';

  const heatColor = getHeatMapColor(value, theme, 2);

  return (
    <PillContainer color={heatColor}>
      <Box
        component="span"
        sx={{
          ...monoStyles,
          fontSize: { xs: '0.5rem', sm: '0.75rem' },
          fontWeight: 600,
          color: getValueColor(value),
        }}
      >
        {value > 0 ? '+' : ''}{formatIntlNumber(value, 2, 1)}
        <Box
          component="span"
          sx={{
            ml: 0.25,
            fontSize: { xs: '0.4375rem', sm: '0.625rem' },
            color: 'text.secondary',
            fontWeight: 400,
          }}
        >
          %p
        </Box>
      </Box>
    </PillContainer>
  );
}, (prevProps, nextProps) => (
  prevProps.cell.getValue() === nextProps.cell.getValue() &&
  prevProps.table.options.meta.isMobile === nextProps.table.options.meta.isMobile
));

// Memoized volatility cell renderer
export const renderVolatilityCell = memo(({ cell }) => {
  const value = cell.getValue();

  if (isUndefined(value)) return '...';

  const isNegative = value < 0;

  return (
    <Box
      component="span"
      sx={{
        ...monoStyles,
        fontSize: { xs: '0.5rem', sm: '0.75rem' },
        fontWeight: 500,
        color: isNegative ? 'error.main' : 'text.primary',
      }}
    >
      {formatIntlNumber(value, 5, 1)}
    </Box>
  );
}, (prevProps, nextProps) => prevProps.cell.getValue() === nextProps.cell.getValue());

// Memoized volume cell renderer with formatting
export const renderVolumeCell = memo(({ cell }) => {
  const value = cell.getValue();

  if (isUndefined(value)) return '...';

  return (
    <Box
      component="span"
      sx={{
        ...monoStyles,
        fontSize: { xs: '0.5rem', sm: '0.75rem' },
        fontWeight: 500,
        color: 'text.secondary',
      }}
    >
      {formatShortNumber(value, 2)}
    </Box>
  );
}, (prevProps, nextProps) => prevProps.cell.getValue() === nextProps.cell.getValue());

// Export memoized versions of other renderers
export const renderNameCell = memo(renderNameCellOriginal, (prevProps, nextProps) => (
  prevProps.row.original.name === nextProps.row.original.name &&
  prevProps.row.original.icon === nextProps.row.original.icon &&
  prevProps.row.original.aiRankRecommendation === nextProps.row.original.aiRankRecommendation
));

export const renderStarCell = memo(renderStarCellOriginal, (prevProps, nextProps) => (
  prevProps.row.original.favoriteAssetId === nextProps.row.original.favoriteAssetId &&
  prevProps.row.original.name === nextProps.row.original.name
));

export const renderWalletStatusCell = memo(renderWalletStatusCellOriginal, (prevProps, nextProps) => (
  JSON.stringify(prevProps.row.original.walletStatus) === JSON.stringify(nextProps.row.original.walletStatus) &&
  prevProps.table.options.meta.isMobile === nextProps.table.options.meta.isMobile
));

// Display names for debugging
renderPremiumCell.displayName = 'MemoizedRenderPremiumCell';
renderPriceCell.displayName = 'MemoizedRenderPriceCell';
renderSpreadCell.displayName = 'MemoizedRenderSpreadCell';
renderVolatilityCell.displayName = 'MemoizedRenderVolatilityCell';
renderVolumeCell.displayName = 'MemoizedRenderVolumeCell';
renderNameCell.displayName = 'MemoizedRenderNameCell';
renderStarCell.displayName = 'MemoizedRenderStarCell';
renderWalletStatusCell.displayName = 'MemoizedRenderWalletStatusCell';
