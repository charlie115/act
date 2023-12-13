import React from 'react';

import Box from '@mui/material/Box';

import noBgLogo from 'assets/png/logo-no-background.png';

export default function BrandLogo({ onClick, size = 140, sx }) {
  return (
    <Box
      onClick={onClick}
      sx={{
        cursor: onClick ? 'pointer' : null,
        display: 'flex',
        alignItems: 'center',
        ...sx,
      }}
    >
      <Box
        component="img"
        src={noBgLogo}
        alt="ArbiCrypto"
        sx={{ width: size }}
      />
    </Box>
  );
}
