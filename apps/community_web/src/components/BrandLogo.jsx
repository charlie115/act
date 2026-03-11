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
        position: 'relative',
        ...sx,
      }}
    >
      <Box
        component="img"
        src={noBgLogo}
        alt="ArbiCrypto"
        sx={{ width: { xs: size * 0.7, md: size }, mr: 0.5 }}
      />
      <Box
        component="small"
        sx={{ alignSelf: 'flex-end', color: 'secondary.main', fontSize: 8 }}
      >
        {process.env.REACT_APP_VERSION}
      </Box>
    </Box>
  );
}
