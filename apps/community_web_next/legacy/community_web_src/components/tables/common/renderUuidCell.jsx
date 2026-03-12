import React from 'react';

import Typography from '@mui/material/Typography';

import truncate from 'lodash/truncate';

export default function renderUuidCell({ column, cell, row, table }) {
  const { isMobile, onUuidClick, selectedUuid } = table.options.meta;

  return (
    <Typography
      onClick={() => {
        if (
          !row.getIsExpanded() ||
          selectedUuid?.[column.id] !== cell.getValue()
        )
          onUuidClick({ column, cell, row });
        else {
          onUuidClick({});
          row.toggleExpanded(false);
        }
      }}
      sx={{
        ...(row.getIsExpanded() && selectedUuid?.[column.id] === cell.getValue()
          ? { color: 'info.main', fontWeight: 700 }
          : {}),
        cursor: 'pointer',
        fontSize: '1em',
        fontStyle: 'italic',
        textDecoration: 'underline',
        textUnderlineOffset: 2,
        ':hover': { color: 'secondary.main' },
      }}
    >
      {isMobile ? truncate(cell.getValue(), { length: 10 }) : cell.getValue()}
    </Typography>
  );
}
