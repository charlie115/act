import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import { useGetDepositBalanceQuery } from 'redux/api/drf/user';
import { useSelector } from 'react-redux';
import formatIntlNumber from 'utils/formatIntlNumber';

export default function DepositBalance() {
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
      setBalance(ownBalance.balance);
    }
  }, [data, user]);

  useEffect(() => {
    if (isSuccess) setReady(true);
  }, [isSuccess]);

  return (
    <Button
      onClick={() => navigate('/bot/deposit')}
      variant="standard"
      color="primary"
      startIcon={<AccountBalanceWalletIcon />}
      sx={{
        borderRadius: '5px',
        height: 36,
        padding: '4px 6px',
        fontWeight: 600,
        textTransform: 'none',
        '&:hover': {
          backgroundColor: 'rgba(25, 118, 210, 0.08)',
        }
      }}
    >
      <Typography 
        sx={{ 
          fontSize: { xs: '0.6rem', md: '0.95rem' },
          fontWeight: 600,
          whiteSpace: 'nowrap'
        }}
      >
        {!ready ? '...' : `${formatIntlNumber(parseFloat(balance || 0), 2, 2)} USDT`}
      </Typography>
    </Button>
  );
}
