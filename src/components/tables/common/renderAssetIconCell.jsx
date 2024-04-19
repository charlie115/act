import React from 'react';

import Box from '@mui/material/Box';

import BlockIcon from '@mui/icons-material/Block';

export default function renderAssetIconCell({ cell, row }) {
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
          sx={{ width: { xs: 14, md: 20 } }}
        />
      ) : (
        <BlockIcon color="secondary" sx={{ fontSize: { xs: 14, md: 20 } }} />
      )}
    </Box>
  );
}
