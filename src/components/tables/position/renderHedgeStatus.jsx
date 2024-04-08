import React from 'react';

import Typography from '@mui/material/Typography';

import i18n from 'configs/i18n';

export default function renderHedgeStatus({ cell }) {
  if (cell.getValue() === null)
    return <Typography sx={{ color: 'secondary.main' }}>N/A</Typography>;
  return (
    <Typography
      sx={{
        color: cell.getValue() ? 'success.light' : 'error.light',
        fontSize: '1.25em',
        textTransform: 'uppercase',
      }}
    >
      {cell.getValue() ? i18n.t('hedge.True') : i18n.t('hedge.False')}
    </Typography>
  );
}
