import React from 'react';

import Typography from '@mui/material/Typography';

export default function renderIdCell({ cell, column, table }) {
  const meta = table.options?.meta;
  const selectedTradeHistoryPair = meta?.selectedTradeHistoryPair;
  return (
    <Typography
      sx={{
        fontSize: '1em',
        ...(selectedTradeHistoryPair?.enter === cell.getValue() ||
        column.id === 'enter_trade_history_uuid'
          ? { color: 'accent.main' }
          : {}),
        ...(selectedTradeHistoryPair?.exit === cell.getValue() ||
        column.id === 'exit_trade_history_uuid'
          ? { color: 'warning.main' }
          : {}),
      }}
    >
      {cell.getValue()}
    </Typography>
  );
}
