import React from 'react';

import Typography from '@mui/material/Typography';

import formatIntlNumber from 'utils/formatIntlNumber';

export default function renderColoredSignedNumberCell({ cell }) {
  return (
    <Typography
      sx={{
        color: cell.getValue() > 0 ? 'success.main' : 'error.main',
        fontSize: '1em',
      }}
    >
      {formatIntlNumber(cell.getValue())}
    </Typography>
  );
}
