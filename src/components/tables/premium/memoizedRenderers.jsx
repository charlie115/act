import React, { memo } from 'react';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import formatIntlNumber from 'utils/formatIntlNumber';
import isUndefined from 'lodash/isUndefined';

// Import original renderers
import renderNameCellOriginal from './renderNameCell';
import renderStarCellOriginal from './renderStarCell';
import renderWalletStatusCellOriginal from './renderWalletStatusCell';

// Memoized premium cell renderer
export const renderPremiumCell = memo(({ cell, row: { original }, table }) => {
  if (isUndefined(cell.getValue())) return '...';
  const { isMobile, isTetherPriceView } = table.options.meta;
  
  return isTetherPriceView ? (
    <Box component="span" sx={{ fontSize: { xs: 8, sm: 12 }, fontWeight: { xs: 400, sm: 700 } }}>
      {formatIntlNumber(
        original.dollar * (1 + cell.getValue() * 0.01), 
        isMobile ? 1 : 2
      )}
    </Box>
  ) : (
    <>
      <Box
        component="span"
        sx={{ fontSize: { xs: 10, sm: 12 }, fontWeight: { xs: 400, sm: 700 } }}
      >
        {formatIntlNumber(cell.getValue(), isMobile ? 2 : 3)}
      </Box>{' '}      
    </>
  );
}, (prevProps, nextProps) => 
  // Custom comparison function for optimization
   (
    prevProps.cell.getValue() === nextProps.cell.getValue() &&
    prevProps.row.original.dollar === nextProps.row.original.dollar &&
    prevProps.table.options.meta.isMobile === nextProps.table.options.meta.isMobile &&
    prevProps.table.options.meta.isTetherPriceView === nextProps.table.options.meta.isTetherPriceView
  )
);

// Memoized price cell renderer
export const renderPriceCell = memo(({ cell, row: { original }, table }) => {
  const value = cell.getValue();
  const { isMobile } = table.options.meta;
  
  if (isUndefined(value)) return '...';
  
  const priceChangePercent = original.c24h || 0;
  const isPositive = priceChangePercent >= 0;
  
  return (
    <>
      <Stack
        alignItems={{ xs: 'flex-start', sm: 'flex-end' }}
        direction={{ xs: 'column', sm: 'row' }}
        spacing={{ xs: 0, sm: 0.5 }}
      >
        <Box sx={{ fontSize: { xs: 9, sm: 12 } }}>
          {formatIntlNumber(cell.getValue(), 1)}
        </Box>
        <Box
          component="small"
          sx={{
            color: original.scr > 0 ? 'success.main' : 'error.main',
            fontWeight: 700,
          }}
        >
          {original.scr > 0 ? '+' : ''}
          {original.scr?.toFixed(2)}%
        </Box>
      </Stack>
      <Box>
        <Box component="small" sx={{ color: 'secondary.main' }}>
          {formatIntlNumber(original.converted_tp, 1)}
        </Box>
      </Box>
    </>
  );
}, (prevProps, nextProps) => (
    prevProps.cell.getValue() === nextProps.cell.getValue() &&
    prevProps.row.original.c24h === nextProps.row.original.c24h &&
    prevProps.table.options.meta.isMobile === nextProps.table.options.meta.isMobile
  ));

// Memoized spread cell renderer
export const renderSpreadCell = memo(({ cell, table }) => {
  const value = cell.getValue();
  const { isMobile } = table.options.meta;
  
  if (isUndefined(value) || value === '') return '...';
  
  return (
    <>
      <Box
        component="span"
        sx={{ fontSize: { xs: 10, sm: 12 }, fontWeight: 400 }}
      >
        {cell.getValue() > 0 ? '+' : ''}
        {formatIntlNumber(cell.getValue(), 2, 1)}
      </Box>{' '}
      <Box component="small" sx={{ color: 'secondary.main' }}>
        %p
      </Box>
    </>
  );
}, (prevProps, nextProps) => (
    prevProps.cell.getValue() === nextProps.cell.getValue() &&
    prevProps.table.options.meta.isMobile === nextProps.table.options.meta.isMobile
  ));

// Memoized volatility cell renderer
export const renderVolatilityCell = memo(({ cell }) => {
  const value = cell.getValue();
  
  if (isUndefined(value)) return '...';
  
  return (
    <Box
      component="span"
      sx={{ fontSize: { xs: 10, sm: 12 }, fontWeight: 400 }}
    >
      {formatIntlNumber(cell.getValue(), 5, 1)}
    </Box>
  );
}, (prevProps, nextProps) => prevProps.cell.getValue() === nextProps.cell.getValue());

// Memoized volume cell renderer
export const renderVolumeCell = memo(({ cell }) => {
  const value = cell.getValue();
  
  if (isUndefined(value)) return '...';
  
  // Use 억 (100 million) for Korean format
  const formattedVolume = value >= 1e8 ? 
    `${Math.floor(value / 1e8).toLocaleString()}억` : 
    formatIntlNumber(value, 0);
  
  return (
    <Box
      component="span"
      sx={{ fontSize: { xs: 8, sm: 12 } }}
    >
      {formattedVolume}
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