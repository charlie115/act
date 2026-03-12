import React from 'react';

import Box from '@mui/material/Box';

import BlockIcon from '@mui/icons-material/Block';

export default function renderAssetIconCell({ cell, table }) {
  const isMobile = table.options.meta?.isMobile;

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        textAlign: 'center',
      }}
    >
      {cell.getValue() ? (
        <Box
          component="img"
          loading="lazy"
          src={cell.getValue()}
          alt=""
          sx={{ width: isMobile ? '0.5rem' : 20 }}
        />
      ) : (
        <BlockIcon color="secondary" sx={{ fontSize: isMobile ? '0.5rem' : 20 }} />
      )}
    </Box>
  );
}
