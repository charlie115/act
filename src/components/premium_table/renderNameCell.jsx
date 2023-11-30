import React from 'react';

import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';

import BlockIcon from '@mui/icons-material/Block';
import InsightsIcon from '@mui/icons-material/Insights';
import StarIcon from '@mui/icons-material/Star';

import Highlighter from 'react-highlight-words';

import isUndefined from 'lodash/isUndefined';

export default function renderNameCell({
  cell,
  row,
  table,
  handleAddFavoriteAsset,
  handleRemoveFavoriteAsset,
  isMobile,
  theme,
}) {
  const isFavorite = !isUndefined(row.original.favoriteAssetId);
  const searchWord = table.getState().globalFilter;

  return (
    <>
      <Box>
        <Stack alignItems="center" direction="row" spacing={{ xs: 0.5, sm: 1 }}>
          <Box>
            {row.original.icon ? (
              <img
                loading="lazy"
                width={isMobile ? '10' : '15'}
                src={row.original.icon}
                alt={row.original.name}
              />
            ) : (
              <BlockIcon color="secondary" sx={{ fontSize: 12 }} />
            )}
          </Box>
          <Box sx={{ fontSize: { xs: 11, sm: 12 } }}>
            <Highlighter
              searchWords={[searchWord]}
              textToHighlight={cell.getValue()}
            />
          </Box>
        </Stack>
      </Box>
      {isMobile && (
        <Stack direction="row" spacing={0.5} sx={{ mt: 0.5 }}>
          <Box>
            <StarIcon
              color={isFavorite ? 'accent' : 'secondary'}
              onClick={(e) => {
                e.stopPropagation();
                if (isFavorite)
                  handleRemoveFavoriteAsset(row.original.favoriteAssetId);
                else handleAddFavoriteAsset(cell.getValue());
              }}
              sx={{
                fontSize: 13,
                '& :hover': { color: theme.palette.accent.main, opacity: 0.5 },
              }}
            />
          </Box>
          <Box>
            <InsightsIcon
              color={row.getIsExpanded() ? 'info' : 'secondary'}
              sx={{ fontSize: 12 }}
            />
          </Box>
        </Stack>
      )}
    </>
  );
}
