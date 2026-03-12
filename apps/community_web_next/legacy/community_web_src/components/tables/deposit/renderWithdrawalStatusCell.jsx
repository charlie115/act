import React from 'react';

import Typography from '@mui/material/Typography';

import { WITHDRAWAL_STATUS_TYPE } from 'constants';

export default function renderWithdrawalStatusCell({ cell }) {
  const value = WITHDRAWAL_STATUS_TYPE[cell.getValue()];
  if (!value) return '-';
  return (
    <Typography
      sx={{ color: value?.color, fontWeight: 700, textTransform: 'uppercase' }}
    >
      {value?.getLabel()}
    </Typography>
  );
}
