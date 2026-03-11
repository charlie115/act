import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Skeleton from '@mui/material/Skeleton';
import Chip from '@mui/material/Chip';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import { useGetDepositBalanceQuery } from 'redux/api/drf/user';
import { useSelector } from 'react-redux';
import formatIntlNumber from 'utils/formatIntlNumber';
import { styled, alpha } from '@mui/material/styles';

// Modern balance display chip
const BalanceChip = styled(Chip)(({ theme }) => ({
  height: 36,
  borderRadius: theme.shape.borderRadius,
  backgroundColor: alpha(theme.palette.primary?.main || '#007cff', 0.1),
  color: theme.palette.primary.main,
  fontWeight: theme.typography.fontWeightMedium,
  transition: theme.transitions.create(['background-color', 'transform'], {
    duration: theme.transitions.duration.short,
  }),
  cursor: 'pointer',
  '& .MuiChip-icon': {
    color: theme.palette.primary.main,
  },
  '&:hover': {
    backgroundColor: alpha(theme.palette.primary?.main || '#007cff', 0.15),
    transform: 'scale(1.02)',
  },
  '&:active': {
    transform: 'scale(0.98)',
  },
}));

// Full width button variant for mobile drawer
const FullWidthButton = styled(Button)(({ theme }) => ({
  width: '100%',
  justifyContent: 'flex-start',
  borderRadius: theme.shape.borderRadius,
  padding: theme.spacing(1.5, 2),
  backgroundColor: alpha(theme.palette.primary?.main || '#007cff', 0.08),
  color: theme.palette.primary.main,
  fontWeight: theme.typography.fontWeightMedium,
  transition: theme.transitions.create(['background-color'], {
    duration: theme.transitions.duration.short,
  }),
  '&:hover': {
    backgroundColor: alpha(theme.palette.primary?.main || '#007cff', 0.12),
  },
}));

export default function DepositBalance({ fullWidth = false }) {
  const navigate = useNavigate();
  const { user } = useSelector((state) => state.auth);
  const [balance, setBalance] = useState();
  const [ready, setReady] = useState(false);

  const { data, isSuccess } = useGetDepositBalanceQuery(
    {},
    { pollingInterval: 5000 }
  );

  useEffect(() => {
    if (data?.results?.length) {
      const ownBalance = data.results.find((item) => item.user === user.uuid);
      setBalance(ownBalance?.balance || 0);
    }
  }, [data, user]);

  useEffect(() => {
    if (isSuccess) setReady(true);
  }, [isSuccess]);

  const handleClick = () => navigate('/bot/deposit');

  const formattedBalance = ready
    ? `${formatIntlNumber(parseFloat(balance || 0), 2, 2)} USDT`
    : null;

  // Full width variant for mobile drawer
  if (fullWidth) {
    return (
      <FullWidthButton
        onClick={handleClick}
        startIcon={<AccountBalanceWalletIcon />}
        disabled={!ready}
      >
        <Typography variant="body2" sx={{ fontWeight: 600 }}>
          {ready ? formattedBalance : 'Loading...'}
        </Typography>
      </FullWidthButton>
    );
  }

  // Chip variant for desktop header
  return ready ? (
    <BalanceChip
      icon={<AccountBalanceWalletIcon />}
      label={formattedBalance}
      onClick={handleClick}
      size="medium"
    />
  ) : (
    <Skeleton
      variant="rounded"
      width={120}
      height={36}
      sx={{ borderRadius: 2 }}
    />
  );
}