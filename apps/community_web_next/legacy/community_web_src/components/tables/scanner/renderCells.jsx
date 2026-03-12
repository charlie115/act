import React from 'react';
import _Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import i18n from 'configs/i18n';

/**
 * Utility function to format numbers without trailing zeros
 */
const formatNumberWithoutTrailingZeros = (value, maximumFractionDigits = 8) => {
  if (value === undefined || value === null) return '-';
  
  // Convert to number if it's a string
  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  
  if (Number.isNaN(numValue)) return '-';
  
  // Convert to string and remove trailing zeros
  const stringValue = numValue.toString();
  
  // If it's a whole number or doesn't have decimals, use toLocaleString normally
  if (!stringValue.includes('.')) {
    return numValue.toLocaleString();
  }
  
  // For decimal numbers, format without trailing zeros
  const formatted = numValue.toLocaleString(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits,
  });
  
  return formatted;
};

/**
 * Renders ATP value divided by 100 million with '억' unit
 */
export const renderAtpCell = ({ getValue, _cell, table }) => {
  const value = getValue();
  const { isMobile } = table.options.meta;
  
  if (value === undefined || value === null) return '-';
  
  // Convert to billions (divide by 100 million)
  const convertedValue = value / 100000000;
  
  return (
    <Typography 
      component="div"
      sx={{ 
        pr: 1
      }}
    >
      {formatNumberWithoutTrailingZeros(convertedValue, 3)}{i18n.t('100M')}
    </Typography>
  );
};

/**
 * Renders funding rate multiplied by 100 with '%' unit
 * Negative values are displayed in red
 */
export const renderFundingRateCell = ({ getValue, _cell, table }) => {
  const value = getValue();
  const { isMobile, theme } = table.options.meta;
  
  if (value === undefined || value === null) return '-';
  
  // Convert to percentage (multiply by 100)
  const percentage = value * 100;
  const isNegative = percentage < 0;
  
  return (
    <Typography
      component="div" 
      sx={{ 
        color: isNegative ? theme.palette.error.main : 'inherit',
        fontSize: isMobile ? '0.4rem !important' : 'inherit',
        pr: 1
      }}
    >
      {formatNumberWithoutTrailingZeros(percentage, 4)}%
    </Typography>
  );
};

/**
 * Renders entry/exit values without trailing zeros
 */
export const renderScannerValueCell = ({ getValue, _cell, table }) => {
  const value = getValue();
  const { isMobile } = table.options.meta;
  
  if (value === undefined || value === null) return '-';
  
  return (
    <Typography
      component="div"
      sx={{ 
        fontWeight: 700,
        pr: 1
      }}
    >
      {formatNumberWithoutTrailingZeros(value, 6)}%
    </Typography>
  );
};

/**
 * Renders iteration values with '회' unit
 */
export const renderIterationCell = ({ getValue, _cell, table }) => {
  const value = getValue();
  const { isMobile } = table.options.meta;
  
  if (value === undefined || value === null) return '-';
  
  return (
    <Typography
      component="div" 
      sx={{ 
        pr: 1
      }}
    >
      {value}{i18n.t('times')}
    </Typography>
  );
};

/**
 * Renders interval values with '초' unit
 */
export const renderIntervalCell = ({ getValue, _cell, table }) => {
  const value = getValue();
  const { isMobile } = table.options.meta;
  
  if (value === undefined || value === null) return '-';
  
  return (
    <Typography
      component="div" 
      sx={{
        pr: 1
      }}
    >
      {value}{i18n.t('secs')}
    </Typography>
  );
}; 