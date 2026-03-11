import React from 'react';

import Typography from '@mui/material/Typography';

export default function renderStatusCell({ cell }) {
  return <Typography sx={{ fontWeight: 700 }}>{cell.getValue()}</Typography>;
}
