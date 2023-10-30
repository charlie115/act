import React from 'react';

import Box from '@mui/material/Box';
import SvgIcon from '@mui/material/SvgIcon';
import Typography from '@mui/material/Typography';

import { styled } from '@mui/material/styles';

import { useSelector } from 'react-redux';

import { ReactComponent as BitcoinCashSvg } from 'assets/svg/bitcoincash.svg';

const NavTitle = styled(Typography)(({ theme }) => ({
  background: `linear-gradient(90deg, ${theme.palette.gradients.primary.main} 35%, ${theme.palette.gradients.primary.state} 65%)`,
  backgroundClip: 'text',
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
  fontWeight: 700,
  letterSpacing: '0.2em',
  textDecoration: 'none',
}));

export default function BrandLogo({
  iconProps,
  iconSize = 24,
  titleVariant = 'h5',
  onClick,
  sx,
}) {
  const theme = useSelector((state) => state.app.theme);

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
      <SvgIcon
        color={theme === 'dark' ? 'white' : 'primary'}
        fontSize="medium"
        sx={{ fontSize: iconSize, mr: 1 }}
        {...iconProps}
      >
        <BitcoinCashSvg />
      </SvgIcon>
      <NavTitle noWrap color="primary" variant={titleVariant}>
        Ar-Kimp
      </NavTitle>
    </Box>
  );
}
