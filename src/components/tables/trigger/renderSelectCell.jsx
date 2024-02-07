import React from 'react';

import Checkbox from '@mui/material/Checkbox';

export default function renderSelectCell({ row }) {
  return (
    <Checkbox
      checked={row.getIsSelected()}
      disabled={row.original.isDeleteLoading}
      indeterminate={row.getIsSomeSelected()}
      onChange={row.getToggleSelectedHandler()}
    />
  );
}
