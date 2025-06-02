import React from 'react';

import Box from '@mui/material/Box';
import Switch from '@mui/material/Switch';

export default function renderAutoRepeatSwitchCell({ cell, row, table }) {
  const { onAutoRepeatClick, isMobile } = table.options.meta;

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center' }}>
      <Switch
        disabled={row.original.trade_capital === null || row.original.trade_capital === undefined}
        edge="end"
        checked={cell.getValue()}
        size={isMobile ? 'small' : 'medium'}
        onChange={(e) => {
          onAutoRepeatClick(e.target.checked, { ...row.original });
        }}
        onClick={(e) => e.stopPropagation()}
        sx={{
          ...(row.original.trade_capital === null ? { opacity: 0.25 } : {}),
          ...(isMobile ? { 
            transform: 'scale(0.8)',
            '& .MuiSwitch-switchBase': {
              padding: '6px',
            },
            '& .MuiSwitch-thumb': {
              width: 16,
              height: 16,
            },
            '& .MuiSwitch-track': {
              borderRadius: 10,
            }
          } : {})
        }}
      />
    </Box>
  );
}
