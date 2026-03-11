import React from 'react';
import Box from '@mui/material/Box';
import Checkbox from '@mui/material/Checkbox';

export default function renderCheckbox({ cell }) {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'center' }}>
      <Checkbox
        checked={cell.getValue()}
        disabled
        size="small"
        sx={{ p: 0.5 }}
      />
    </Box>
  );
}
