import React, { useEffect, useState } from 'react';

import ClickAwayListener from '@mui/material/ClickAwayListener';
import Collapse from '@mui/material/Collapse';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';
import OutlinedInput from '@mui/material/OutlinedInput';
import Stack from '@mui/material/Stack';

import CloseIcon from '@mui/icons-material/Close';
import SearchIcon from '@mui/icons-material/Search';

import { useTranslation } from 'react-i18next';

import { useDebounce } from '@uidotdev/usehooks';

export default function CollapsibleSearch({ onChange }) {
  const { t } = useTranslation();

  const [open, setOpen] = useState(false);
  const [value, setValue] = useState('');
  const debouncedValue = useDebounce(value, 1000);

  useEffect(() => {
    onChange(debouncedValue);
  }, [debouncedValue]);

  return (
    <ClickAwayListener
      onClickAway={() => {
        if (!value) setOpen(false);
      }}
    >
      <Stack direction="row" sx={{ p: 1 }}>
        <Collapse unmountOnExit in={open} orientation="horizontal">
          <OutlinedInput
            autoFocus={open}
            size="small"
            placeholder={t('Search')}
            onChange={(e) => setValue(e.target.value)}
            value={value}
            startAdornment={
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            }
            endAdornment={
              <InputAdornment position="end">
                <IconButton
                  edge="end"
                  onClick={() => {
                    setValue('');
                    onChange('');
                  }}
                >
                  <CloseIcon />
                </IconButton>
              </InputAdornment>
            }
          />
        </Collapse>
        {!open && (
          <IconButton onClick={() => setOpen(!open)}>
            <SearchIcon />
          </IconButton>
        )}
      </Stack>
    </ClickAwayListener>
  );
}
