import React from 'react';

import { DateTime } from 'luxon';

export default function renderDateCell({ cell }) {
  const dateValue = cell.getValue();

  // Check if dateValue is null or undefined
  if (dateValue == null) { // Use == null to check for both undefined and null
    return '-';
  }
  
  // Explicitly treat the input as UTC if it doesn't have timezone info
  const dateTime = DateTime.fromISO(dateValue, { zone: 'utc' });

  // Also check if the date parsed is valid, return '-' if not
  if (!dateTime.isValid) {
    console.warn(`Invalid dateValue encountered: ${dateValue}`);
    return '-';
  }
  
  // Convert to local timezone
  const localDateTime = dateTime.setZone('local');
  
  // Display with timezone information
  return (
    <small>
      {localDateTime.toLocaleString(DateTime.DATETIME_MED)}
    </small>
  );
}
