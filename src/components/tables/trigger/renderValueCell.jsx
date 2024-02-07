import React from 'react';

import Box from '@mui/material/Box';

import i18n from 'configs/i18n';

export default function renderValueCell({ cell, row: { original } }) {
  return (
    <>
      <Box component="span" sx={{ fontWeight: 700 }}>
        {cell.getValue()}
      </Box>{' '}
      <small>{original.isTether ? i18n.t('KRW') : '%'}</small>
    </>
  );
}
