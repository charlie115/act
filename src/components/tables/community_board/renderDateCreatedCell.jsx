import React from 'react';

import Typography from '@mui/material/Typography';

import { DateTime } from 'luxon';

export default function renderDateCreatedCell({ cell }) {
  return (
    <Typography>
      {
        DateTime.fromISO(cell.getValue()).toLocaleString(
          DateTime.DATE_MED_WITH_WEEKDAY
        )
        // .toRelativeCalendar()
        // .toLocaleUpperCase()
      }
    </Typography>
  );
}
