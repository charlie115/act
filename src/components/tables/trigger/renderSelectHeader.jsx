import React from 'react';

import Checkbox from '@mui/material/Checkbox';

export default function renderSelectHeader({ table }) {
  console.log('table: ', table);
  return (
    <Checkbox
      checked={table.getIsAllPageRowsSelected()}
      indeterminate={table.getIsSomePageRowsSelected()}
      onChange={table.getToggleAllPageRowsSelectedHandler()}
    />
  );
}
