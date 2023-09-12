import React from 'react';

import { useNavigate } from 'react-router-dom';

import Box from '@mui/material/Box';
import SvgIcon from '@mui/material/SvgIcon';
import Typography from '@mui/material/Typography';

import { styled } from '@mui/material/styles';

import { ReactComponent as BitcoinCashSvg } from 'assets/svg/bitcoincash.svg';

const NavTitle = styled(Typography)(({ theme }) => ({
  background: `linear-gradient(90deg, ${theme.palette.gradients.primary.main} 40%, ${theme.palette.gradients.primary.state} 50%)`,
  backgroundClip: 'text',
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
  fontWeight: 700,
  letterSpacing: '0.2em',
  textDecoration: 'none',
}));

export default function BrandLogo({ iconSize = 24, nameVariant = 'h5', sx }) {
  const navigate = useNavigate();

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', ...sx }}>
      <SvgIcon
        color="white"
        fontSize="medium"
        sx={{ cursor: 'pointer', fontSize: iconSize, mr: 1 }}
        onClick={() => navigate('/')}
      >
        <BitcoinCashSvg />
      </SvgIcon>
      <NavTitle
        noWrap
        color="primary"
        variant={nameVariant}
        component="a"
        href="/"
        sx={{ mr: 4 }}
      >
        AR-Kimp
      </NavTitle>
    </Box>
  );
}
