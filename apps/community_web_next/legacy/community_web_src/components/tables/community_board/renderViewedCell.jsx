import React from 'react';

import Typography from '@mui/material/Typography';

export default function renderViewedCell({ cell, row: { original } }) {
  if (original.loggedInUser === original.user) return null;

  return !cell.getValue() ? (
    <Typography sx={{ color: 'error.main', fontSize: 10, textAlign: 'center' }}>
      NEW
    </Typography>
  ) : null;
}
