import React from 'react';

import Box from '@mui/material/Box';

export default function TabPanel({ id, children, value, index, ...props }) {
  return (
    <div
      id={`${id}-tabpanel-${index}`}
      aria-labelledby={`${id}-tab-${index}`}
      hidden={value !== index}
      role="tabpanel"
      {...props}
    >
      <Box sx={{ display: value === index ? 'block' : 'none' }}>{children}</Box>
    </div>
  );
}
