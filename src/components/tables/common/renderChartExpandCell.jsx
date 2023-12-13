import React from 'react';

import InsightsIcon from '@mui/icons-material/Insights';

export default function renderChartExpandCell({ row }) {
  return (
    <InsightsIcon
      color={row.getIsExpanded() ? 'info' : ''}
      sx={{ fontSize: { md: '0.65rem', lg: 14 } }}
    />
  );
}
