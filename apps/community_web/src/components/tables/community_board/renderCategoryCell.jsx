import React from 'react';

import CircleIcon from '@mui/icons-material/Circle';

import { POST_CATEGORY_LIST } from 'constants/lists';

export default function renderCategoryCell({ cell }) {
  const category = POST_CATEGORY_LIST.find((o) => o.value === cell.getValue());

  return (
    <>
      <CircleIcon sx={{ color: category?.color, fontSize: 12 }} />{' '}
      {category?.getLabel()}
    </>
  );
}
