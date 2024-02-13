import React from 'react';

import InsightsIcon from '@mui/icons-material/Insights';

export default function renderChartExpandCell({ cell, row }) {
  if (cell.getValue() === false) return null;
  return (
    <InsightsIcon
      color={row.getIsExpanded() ? 'info' : ''}
      sx={{ fontSize: { xs: '1em', md: '0.65rem', lg: 14 } }}
    />
  );
}
