import React from 'react';

import { DateTime } from 'luxon';

export default function renderDateCell({ cell }) {
  const dateValue = cell.getValue();
  
  // Explicitly treat the input as UTC if it doesn't have timezone info
  const dateTime = DateTime.fromISO(dateValue, { zone: 'utc' });
  
  // Convert to local timezone
  const localDateTime = dateTime.setZone('local');
  
  // Display with timezone information
  return (
    <small>
      {localDateTime.toLocaleString(DateTime.DATETIME_MED)}
    </small>
  );
}
