import React from 'react';

import Box from '@mui/material/Box';

import BlockIcon from '@mui/icons-material/Block';

export default function renderIconCell({ cell, row, isMobile }) {
  return (
    <Box sx={{ display: 'flex', textAlign: 'center' }}>
      {cell.getValue() ? (
        <img
          loading="lazy"
          width={isMobile ? '12' : '20'}
          src={cell.getValue()}
          alt={row.original.name}
        />
      ) : (
        <BlockIcon color="secondary" sx={{ fontSize: 12 }} />
      )}
    </Box>
  );
}
