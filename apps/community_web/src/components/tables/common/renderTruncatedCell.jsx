import React from 'react';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import { useTranslation } from 'react-i18next';



const truncateMiddle = (str, startChars = 5, endChars = 5) => {
  if (!str) return '-';
  if (str.length <= startChars + endChars) return str;
  return `${str.slice(0, startChars)}...${str.slice(-endChars)}`;
};

const renderTruncatedCell = ({
  cell,
  tooltipText = 'Copy',
  startChars = 5,
  endChars = 5,
  showCopyButton = true
}) => {
  const value = cell.getValue();
  const { t } = useTranslation();

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
      <Typography>{truncateMiddle(value, startChars, endChars)}</Typography>
      {showCopyButton && value && (
        <Tooltip title={t(tooltipText)}>
          <IconButton 
            size="small" 
            onClick={() => navigator.clipboard.writeText(value)}
          >
            <ContentCopyIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      )}
    </Box>
  );
};

export default renderTruncatedCell;