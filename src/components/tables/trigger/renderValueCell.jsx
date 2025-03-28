import React from 'react';

import Box from '@mui/material/Box';
import AddIcon from '@mui/icons-material/Add';

import i18n from 'configs/i18n';

export default function renderValueCell({ cell, column, row: { original }, table }) {
  const isMobile = table.options.meta?.isMobile;

  if (original.add)
    return (
      <AddIcon
        color={column.id === 'entry' ? 'accent' : 'warning'}
        className="animate__animated animate__heartBeat animate__infinite"
      />
    );
  return (
    <Box
      component="span"
      sx={{
        fontWeight: 700,
        fontSize: isMobile ? 6 : 'inherit',
      }}
    >
      {cell.getValue()}{' '}
      {original.isTether ? i18n.t('KRW') : '%'}
    </Box>
  );
}
