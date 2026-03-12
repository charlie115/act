import React, { useCallback, useEffect, useState } from 'react';

import ClickAwayListener from '@mui/material/ClickAwayListener';
import Collapse from '@mui/material/Collapse';
import IconButton from '@mui/material/IconButton';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';

import CalendarTodayIcon from '@mui/icons-material/CalendarToday';

import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { PickersDay } from '@mui/x-date-pickers/PickersDay';

import { DateTime } from 'luxon';
import { useTranslation } from 'react-i18next';

import { useDebounce } from '@uidotdev/usehooks';
import debounce from 'lodash/debounce';

function CustomDay({ day, range, selected, ...props }) {
  const timestamp = day.toMillis();
  return (
    <PickersDay
      {...props}
      selected={
        selected || (timestamp >= range?.from && timestamp <= range?.to)
      }
      day={day}
    />
  );
}

function CustomTextField({ range, sx, ...props }) {
  const [value, setValue] = useState('');

  useEffect(() => {
    if (range) {
      const from = range.from
        ? DateTime.fromMillis(range.from).toFormat('yyyy/MM/dd')
        : '';
      const to = range.to
        ? DateTime.fromMillis(range.to).toFormat('yyyy/MM/dd')
        : '';
      setValue(`${from}—${to}`);
    } else setValue('');
  }, [range, props.value]);

  return (
    <TextField
      {...props}
      size="small"
      value={value}
      sx={{ ...sx, width: 250 }}
    />
  );
}

export default function DateRangePicker({ onChange, onClear }) {
  const { t } = useTranslation();

  const [collapsed, setCollapsed] = useState(true);

  const [open, setOpen] = useState(false);
  const [range, setRange] = useState();
  const debouncedRange = useDebounce(range, 500);

  const handleOpen = () => setOpen(true);
  const handleClose = () => {
    if (!range || (range?.from && range?.to)) setOpen(false);
    if (!range || !(range?.from || range?.to))
      setTimeout(() => setCollapsed(true), 500);
  };

  const handleDayToggle = (e) => {
    const { timestamp } = e.target.dataset;
    if (e.type === 'click') {
      if (!range || (range?.from && range?.to))
        setRange({ from: Number(timestamp), to: null });
      else if (range?.from && !range?.to) {
        if (timestamp >= range.from)
          setRange({ ...range, to: Number(timestamp) });
        else setRange({ from: Number(timestamp), to: null });
      }
    }
  };

  const debouncedOnClear = useCallback(
    debounce(onClear, 1000, { leading: false, trailing: true }),
    []
  );

  useEffect(() => {
    if (debouncedRange?.from && debouncedRange?.to) onChange(debouncedRange);
  }, [debouncedRange]);

  useEffect(() => {
    let timeout;
    if (!collapsed) timeout = setTimeout(() => setOpen(true), 500);

    return () => {
      if (timeout) clearTimeout(timeout);
    };
  }, [collapsed]);

  return (
    <ClickAwayListener onClickAway={handleClose}>
      <Stack direction="row">
        <Collapse in={!collapsed} orientation="horizontal">
          <DatePicker
            disableFuture
            showDaysOutsideCurrentMonth
            closeOnSelect={false}
            open={open}
            timezone={DateTime.now().zoneName}
            minDate={DateTime.now().minus({ weeks: 2 })}
            onClose={handleClose}
            onAccept={handleClose}
            slots={{ day: CustomDay, textField: CustomTextField }}
            slotProps={{
              day: { onClick: handleDayToggle, range },
              field: {
                clearable: true,
                onClear: () => {
                  setRange(null);
                  debouncedOnClear(range);
                },
              },
              openPickerButton: { onClick: handleOpen },
              textField: {
                onClick: handleOpen,
                placeholder: t('Select date range'),
                size: 'small',
                range,
              },
            }}
          />
        </Collapse>
        {collapsed && (
          <IconButton onClick={() => setCollapsed(false)}>
            <CalendarTodayIcon />
          </IconButton>
        )}
      </Stack>
    </ClickAwayListener>
  );
}
