import React from 'react';

export default function renderExpandCell({ cell, row, table }) {
  if (cell.getValue() === false) return null;
  return (
    <table.options.meta.expandIcon
      color={row.getIsExpanded() ? 'info' : ''}
      sx={{ fontSize: { xs: '1em', md: '0.65rem', lg: 14 } }}
    />
  );
}
