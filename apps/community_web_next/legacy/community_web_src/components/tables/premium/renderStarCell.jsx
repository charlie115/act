import React from 'react';

import Tooltip from '@mui/material/Tooltip';

import StarIcon from '@mui/icons-material/Star';

import isUndefined from 'lodash/isUndefined';

import i18n from 'configs/i18n';

export default function renderStarCell({ cell, row, table }) {
  const isFavorite = !isUndefined(cell.getValue());

  const { onAddFavoriteAsset, onRemoveFavoriteAsset, theme } =
    table.options.meta;

  return (
    <Tooltip
      title={
        isFavorite
          ? i18n.t('Remove from favorites')
          : i18n.t('Add to favorites')
      }
    >
      <StarIcon
        color={isFavorite ? 'accent' : 'secondary'}
        onClick={(e) => {
          e.stopPropagation();
          if (isFavorite) onRemoveFavoriteAsset(cell.getValue());
          else onAddFavoriteAsset(row.original.name);
        }}
        sx={{
          fontSize: { sm: '0.75rem', md: 16, lg: 20 },
          ':hover': { color: theme.palette.accent.main, opacity: 0.5 },
        }}
      />
    </Tooltip>
  );
}
