import React from 'react';

import Typography from '@mui/material/Typography';

import PersonIcon from '@mui/icons-material/Person';

export default function renderViewedCell({ cell, row: { original } }) {
  if (original.loggedInUser === original.user)
    return (
      <PersonIcon
        color="secondary"
        sx={{ fontSize: 12, textAlign: 'center' }}
      />
    );

  return !cell.getValue() ? (
    <Typography sx={{ color: 'error.main', fontSize: 10 }}>NEW</Typography>
  ) : null;
}
