import React from 'react';

import Typography from '@mui/material/Typography';

import { DateTime } from 'luxon';

export default function renderDateCreatedCell({ cell }) {
  return (
    <Typography sx={{ fontSize: { xs: '0.9em', md: '1em' } }}>
      {
        DateTime.fromISO(cell.getValue()).toLocaleString(
          DateTime.DATETIME_SHORT
        )
        // .toRelativeCalendar()
        // .toLocaleUpperCase()
      }
    </Typography>
  );
}
