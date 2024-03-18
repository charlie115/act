import React from 'react';

import IconButton from '@mui/material/IconButton';

import NotInterestedIcon from '@mui/icons-material/NotInterested';

export default function renderActionIconCell({
  cell,
  row,
  table: { options },
}) {
  const Icon = options.meta?.action?.icon || NotInterestedIcon;
  if (cell.getValue() === false) return null;
  return (
    <IconButton
      onClick={() => {
        if (options.meta?.action?.onClick)
          options.meta?.action?.onClick({ cell, row });
      }}
      sx={{ p: 0.25 }}
      {...options.meta?.action?.iconProps}
    >
      <Icon
        sx={{ fontSize: { xs: '1em', md: '0.65rem', lg: 14 } }}
        {...options.meta?.action?.iconProps}
      />
    </IconButton>
  );
}
