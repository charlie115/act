import React from 'react';

import Box from '@mui/material/Box';
import Switch from '@mui/material/Switch';

export default function renderAutoRepeatCell({ cell, row, table }) {
  const { onAutoRepeatClick } = table.options.meta;

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center' }}>
      <Switch
        edge="end"
        checked={cell.getValue()}
        // checked={cell.getValue()}
        size="small"
        onChange={(e) => {
          onAutoRepeatClick(e.target.checked, { ...row.original });
          // dispatch(toggleNotification(e.target.checked));
          // handleClose();
        }}
        onClick={(e) => e.stopPropagation()}
      />
    </Box>
  );
}
