import React from 'react';

import { DateTime } from 'luxon';

export default function renderDate({ cell }) {
  return (
    <small>
      {DateTime.fromISO(cell.getValue()).toLocaleString(DateTime.DATETIME_MED)}
    </small>
  );
}
