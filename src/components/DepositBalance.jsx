import React, { useEffect, useState } from 'react';

import { useNavigate } from 'react-router-dom';

import IconButton from '@mui/material/IconButton';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';

import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';

import { useGetDepositBalanceQuery } from 'redux/api/drf/user';

import { useSelector } from 'react-redux';

import formatIntlNumber from 'utils/formatIntlNumber';

export default function DepositBalance() {
  const navigate = useNavigate();

  const { user } = useSelector((state) => state.auth);

  const [balance, setBalance] = useState();

  const { data, isFetching } = useGetDepositBalanceQuery(
    {},
    { pollingInterval: 5000 }
  );

  useEffect(() => {
    if (data?.results?.length) {
      const ownBalance = data.results.find((item) => item.user === user.uuid);
      setBalance(ownBalance.balance);
    }
  }, [data, user]);

  return (
    <Stack direction="row" alignItems="center" sx={{ px: 4 }}>
      <IconButton
        color="info"
        onClick={() => navigate('/bot', { state: { defaultTab: 'deposit' } })}
      >
        <AccountBalanceWalletIcon />
      </IconButton>
      {isFetching ? (
        '...'
      ) : (
        <Typography sx={{ fontSize: '1.15em', fontWeight: 700 }}>
          {balance ? formatIntlNumber(parseFloat(balance), 2, 2) : 0}
        </Typography>
      )}
    </Stack>
  );
}
