import React, { useState } from 'react';

import Box from '@mui/material/Box';
import ClickAwayListener from '@mui/material/ClickAwayListener';
import Collapse from '@mui/material/Collapse';
import IconButton from '@mui/material/IconButton';
import Stack from '@mui/material/Stack';

import CalendarTodayIcon from '@mui/icons-material/CalendarToday';

import DateRangePicker from 'components/DateRangePicker';

export default function CollapsibleDateRangePicker() {
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState(null);

  return (
    <ClickAwayListener
      onClickAway={() => {
        if (!value) setOpen(false);
      }}
    >
      <Box>CollapsibleDateRangePicker</Box>
    </ClickAwayListener>
  );
}
