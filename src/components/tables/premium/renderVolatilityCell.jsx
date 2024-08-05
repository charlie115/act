import React from 'react';

import formatIntlNumber from 'utils/formatIntlNumber';

import isUndefined from 'lodash/isUndefined';

export default function renderVolatilityCell({ cell }) {
  return isUndefined(cell.getValue()) ? (
    '...'
  ) : (
    <>{formatIntlNumber(cell.getValue(), 5, 1)}</>
  );
}
