import React from 'react';

import { useTranslation } from 'react-i18next';

import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import Chip from '@mui/material/Chip';

import BlockIcon from '@mui/icons-material/Block';
import InsightsIcon from '@mui/icons-material/Insights';
import StarIcon from '@mui/icons-material/Star';
import SmartToyIcon from '@mui/icons-material/SmartToy';

import Highlighter from 'react-highlight-words';

import isUndefined from 'lodash/isUndefined';

export default function renderNameCell({ cell, row, table }) {
  const isFavorite = !isUndefined(row.original.favoriteAssetId);
  const searchWord = table.getState().globalFilter;
  const { t } = useTranslation();

  const { onAddFavoriteAsset, onRemoveFavoriteAsset, isMobile, theme } =
    table.options.meta;
    
  const aiRecommendation = row.original.aiRankRecommendation;
  
  // Map risk level to colors
  const getRiskLevelColor = (riskLevel) => {
    switch(riskLevel) {
      case 1: return theme.palette.success.main; // Low risk
      case 2: return theme.palette.warning.main; // Medium risk
      case 3: return theme.palette.error.main;   // High risk
      default: return theme.palette.info.main;
    }
  };
  
  const getAiTooltipContent = () => {
    if (!aiRecommendation) return '';
    
    return (
      <>
        <div><strong>{t('Rank')}: {aiRecommendation.rank}</strong></div>
        <div><strong>{t('Risk Level')}: {aiRecommendation.risk_level}</strong></div>
        <div>{aiRecommendation.explanation}</div>
      </>
    );
  };

  return (
    <>
      <Box>
        <Stack alignItems="center" direction="row" spacing={{ xs: 0.5, sm: 1 }}>
          <Box>
            {row.original.icon ? (
              <img
                loading="lazy"
                width={isMobile ? '8' : '15'}
                src={row.original.icon}
                alt={cell.getValue()}
              />
            ) : (
              <BlockIcon color="secondary" sx={{ fontSize: isMobile ? 10 : 12 }} />
            )}
          </Box>
          <Box sx={{ fontSize: { xs: 9, sm: 12 } }}>
            <Highlighter
              searchWords={[searchWord]}
              textToHighlight={cell.getValue()}
            />
          </Box>
          {aiRecommendation && (
            <Tooltip title={getAiTooltipContent()} arrow placement="right">
              {isMobile ? (
                <SmartToyIcon 
                  sx={{
                    fontSize: 9,
                    color: getRiskLevelColor(aiRecommendation.risk_level),
                    ml: 0.2
                  }}
                />
              ) : (
                <Chip 
                  icon={<SmartToyIcon fontSize="small" />}
                  label={t('Recommended')}
                  size="small"
                  sx={{ 
                    fontSize: 10,
                    height: 13,
                    bgcolor: getRiskLevelColor(aiRecommendation.risk_level),
                    color: '#fff',
                    '& .MuiChip-icon': {
                      fontSize: 14,
                      color: '#fff',
                      marginLeft: 0.1
                    }
                  }}
                  variant="filled"
                />
              )}
            </Tooltip>
          )}
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
                  onRemoveFavoriteAsset(row.original.favoriteAssetId);
                else onAddFavoriteAsset(cell.getValue());
              }}
              sx={{ fontSize: 13 }}
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
