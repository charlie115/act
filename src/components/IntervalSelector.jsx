import React, { useEffect, useState } from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';

import { styled } from '@mui/material/styles';

import { useTranslation } from 'react-i18next';

import { useDebounce } from '@uidotdev/usehooks';

import { INTERVAL_LIST } from 'constants/lists';

const ToggleBtn = styled(ToggleButton)(() => ({
  fontSize: 11,
  textTransform: 'none',
}));

function IntervalSelector({ defaultValue, disabled, onChange }) {
  const { t } = useTranslation();

  const [selectedIdx, setSelectedIdx] = useState(
    defaultValue
      ? INTERVAL_LIST.findIndex((o) => o.value === defaultValue)
      : null
  );
  const debouncedSelectedIdx = useDebounce(selectedIdx, 1000);

  const [anchorEl, setAnchorEl] = useState(null);

  useEffect(() => {
    if (debouncedSelectedIdx !== null && onChange)
      onChange(INTERVAL_LIST[debouncedSelectedIdx].value);
  }, [debouncedSelectedIdx]);

  return (
    <Box>
      <ToggleButtonGroup
        exclusive
        disabled={disabled}
        value={selectedIdx}
        onChange={(e, newIdx) => {
          e.stopPropagation();
          setSelectedIdx(newIdx);
        }}
        color="secondary"
        size="small"
        sx={{ display: { xs: 'none', sm: 'inline-flex' } }}
      >
        {INTERVAL_LIST.map((interval, idx) => (
          <ToggleBtn key={interval.value} value={idx} sx={{ py: 0 }}>
            {interval.getLabel()}
          </ToggleBtn>
        ))}
      </ToggleButtonGroup>
      <Button
        disabled={disabled}
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
        }}
      >
        {selectedIdx !== null
          ? INTERVAL_LIST[selectedIdx].getLabel()
          : t('Intervals')}
      </Button>
      <Menu
        anchorEl={anchorEl}
        open={!!anchorEl}
        onClose={() => setAnchorEl(null)}
        sx={{ display: { xs: 'inline-flex', sm: 'none' } }}
      >
        {INTERVAL_LIST.map((interval, idx) => (
          <MenuItem
            key={interval.value}
            disabled={selectedIdx === idx}
            selected={idx === selectedIdx}
            onClick={() => {
              setSelectedIdx(idx);
              setAnchorEl(null);
            }}
          >
            {interval.getLabel()}
          </MenuItem>
        ))}
      </Menu>
    </Box>
  );
}

export default React.memo(IntervalSelector);
