import React from 'react';

import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';

import PersonIcon from '@mui/icons-material/Person';

export default function renderUserCell({ cell }) {
  return (
    <Stack alignItems="center" direction="row" spacing={0.5}>
      <PersonIcon fontSize="small" />
      <Box>{cell.getValue()}</Box>
    </Stack>
  );
}
