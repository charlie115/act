import React from 'react';
import Box from '@mui/material/Box';

export default function renderMarketCodeHeader({ column, table }) {
  const { marketCodes } = table?.options?.meta || {};
  const marketCode = marketCodes?.[column.id];
  
  if (!marketCode) {
    return <span>{column.id}</span>;
  }
  
  const isMobile = table?.options?.meta?.isMobile;
  
  return (
    <Box sx={{ 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center', 
      gap: 0.5,
      fontSize: isMobile ? '0.35rem' : 'inherit',
      width: '100%'
    }}>
      {marketCode.icon}
      <span>{marketCode.getLabel()}</span>
    </Box>
  );
}
