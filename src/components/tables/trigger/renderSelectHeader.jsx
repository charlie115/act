import React from 'react';

import Checkbox from '@mui/material/Checkbox';

export default function renderSelectHeader({ table }) {
  return (
    <Checkbox
      checked={table.getIsAllPageRowsSelected()}
      indeterminate={table.getIsSomePageRowsSelected()}
      onChange={table.getToggleAllPageRowsSelectedHandler()}
      size="small"
      sx={{ p: 0.5 }}
    />
  );
}
