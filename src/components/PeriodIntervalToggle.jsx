import React, { useEffect, useState } from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';

import { styled } from '@mui/material/styles';

import { useTranslation } from 'react-i18next';

import { DATA_PERIOD_INTERVALS } from 'constants/lists';

const IntervalToggleBtn = styled(ToggleButton)(() => ({
  fontSize: 11,
  textTransform: 'none',
}));

function PeriodIntervalToggle({ value, onChange }) {
  const { i18n, t } = useTranslation();

  const [selectedIdx, setSelectedIdx] = useState(
    value ? DATA_PERIOD_INTERVALS.findIndex((o) => o.value === value) : null
  );

  const [intervals, setIntervals] = useState([]);

  const [anchorEl, setAnchorEl] = useState(null);

  useEffect(() => {
    if (value && intervals.length > 0 && onChange)
      setSelectedIdx(DATA_PERIOD_INTERVALS.findIndex((o) => o.value === value));
  }, [value]);

  useEffect(() => {
    if (
      selectedIdx !== null &&
      value !== DATA_PERIOD_INTERVALS[selectedIdx].value &&
      onChange
    )
      onChange(DATA_PERIOD_INTERVALS[selectedIdx].value);
  }, [selectedIdx]);

  useEffect(() => {
    setIntervals(
      DATA_PERIOD_INTERVALS.map((interval) => ({
        label: interval.getLabel(),
        ...interval,
      }))
    );
  }, [i18n.language]);

  if (intervals.length === 0) return null;

  return (
    <Box sx={{ flex: 0 }}>
      <ToggleButtonGroup
        exclusive
        value={selectedIdx}
        onChange={(e, newIdx) => setSelectedIdx(newIdx)}
        color="secondary"
        size="small"
        sx={{ display: { xs: 'none', sm: 'inline-flex' } }}
      >
        {intervals.map((interval, idx) => (
          <IntervalToggleBtn key={interval.value} value={idx} sx={{ py: 0 }}>
            {interval.label}
          </IntervalToggleBtn>
        ))}
      </ToggleButtonGroup>
      <Button
        color="secondary"
        size="small"
        variant="outlined"
        onClick={(e) => {
          e.stopPropagation();
          setAnchorEl(e.currentTarget);
        }}
        sx={{
          display: { xs: 'inline-flex', sm: 'none' },
          fontSize: 11,
          px: 0.5,
          py: 0,
          textTransform:
            selectedIdx !== null && selectedIdx <= 6 ? 'none' : 'uppercase',
        }}
      >
        {selectedIdx !== null ? intervals[selectedIdx].label : t('Intervals')}
      </Button>
      <Menu
        anchorEl={anchorEl}
        open={!!anchorEl}
        onClose={() => setAnchorEl(null)}
        sx={{ display: { xs: 'inline-flex', sm: 'none' } }}
      >
        {intervals.map((interval, idx) => (
          <MenuItem
            key={interval.value}
            disabled={selectedIdx === idx}
            selected={idx === selectedIdx}
            onClick={() => {
              setSelectedIdx(idx);
              setAnchorEl(null);
            }}
          >
            {interval.label}
          </MenuItem>
        ))}
      </Menu>
    </Box>
  );
}

export default React.memo(PeriodIntervalToggle);
