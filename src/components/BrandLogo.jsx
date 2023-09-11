import React from 'react';

import Box from '@mui/material/Box';
import SvgIcon from '@mui/material/SvgIcon';
import Typography from '@mui/material/Typography';

import { styled } from '@mui/material/styles';

import { ReactComponent as BitcoinCashSvg } from 'assets/svg/bitcoincash.svg';

const NavTitle = styled(Typography)(() => ({
  mr: 4,
  fontWeight: 700,
  letterSpacing: '0.2em',
  textDecoration: 'none',
}));

export default function BrandLogo({ iconSize = 24, nameVariant = 'h5', sx }) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', ...sx }}>
      <SvgIcon
        color="primary"
        fontSize="medium"
        sx={{ fontSize: iconSize, mr: 1 }}
      >
        <BitcoinCashSvg />
      </SvgIcon>
      <NavTitle
        noWrap
        color="primary"
        variant={nameVariant}
        component="a"
        href="/"
      >
        AR-Kimp
      </NavTitle>
    </Box>
  );
}
