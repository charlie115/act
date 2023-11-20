import React, { useCallback, useEffect, useState } from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';

import { styled } from '@mui/material/styles';

import { useTranslation } from 'react-i18next';

import debounce from 'lodash/debounce';
import isPlainObject from 'lodash/isPlainObject';

import { KLINE_DATA_TYPE } from 'constants/lists';

const ToggleBtn = styled(ToggleButton)(() => ({
  fontSize: 11,
  padding: '0 15px',
  textTransform: 'none',
}));

function KlineDataSelector({
  defaultValue,
  disabled,
  isKimpExchange,
  isTetherPriceView,
  onChange,
}) {
  const { i18n, t } = useTranslation();

  const [selectedIdx, setSelectedIdx] = useState(
    defaultValue
      ? KLINE_DATA_TYPE.findIndex((o) => o.value === defaultValue)
      : null
  );

  const [kLineData, setKLineData] = useState([]);

  const [anchorEl, setAnchorEl] = useState(null);

  const debouncedOnChange = useCallback(
    debounce(onChange, 1000, {
      leading: true,
      trailing: true,
    }),
    []
  );

  useEffect(() => {
    if (selectedIdx !== null && onChange)
      debouncedOnChange(KLINE_DATA_TYPE[selectedIdx].value);
  }, [selectedIdx]);

  useEffect(() => {
    setKLineData(
      KLINE_DATA_TYPE.map((datum) => ({
        ...datum,
        label: isKimpExchange
          ? [isTetherPriceView ? datum.getTetherLabel() : datum.getKimpLabel()]
          : datum.label,
      }))
    );
  }, [i18n.language, isKimpExchange, isTetherPriceView]);

  if (kLineData.length === 0) return null;

  return (
    <Box>
      <ToggleButtonGroup
        exclusive
        disabled={!isPlainObject(disabled) && disabled}
        value={selectedIdx}
        onChange={(e, newIdx) => {
          e.stopPropagation();
          setSelectedIdx(newIdx);
        }}
        color="secondary"
        size="small"
        sx={{ display: { xs: 'none', md: 'inline-flex' } }}
      >
        {kLineData.map((item, idx) => (
          <ToggleBtn
            key={item.value}
            disabled={disabled?.[item.value]}
            value={idx}
            sx={{ px: 1, py: 0 }}
          >
            {item.label}
          </ToggleBtn>
        ))}
      </ToggleButtonGroup>
      <Button
        color="secondary"
        size="small"
        variant="outlined"
        disabled={!isPlainObject(disabled) && disabled}
        onClick={(e) => {
          e.stopPropagation();
          setAnchorEl(e.currentTarget);
        }}
        sx={{
          display: { xs: 'inline-flex', md: 'none' },
          fontSize: 11,
          px: 0.5,
          py: 0,
        }}
      >
        {selectedIdx !== null ? kLineData[selectedIdx].label : t('Intervals')}
      </Button>
      <Menu
        anchorEl={anchorEl}
        open={!!anchorEl}
        onClose={() => setAnchorEl(null)}
        sx={{ display: { xs: 'inline-flex', md: 'none' } }}
      >
        {kLineData.map((item, idx) => (
          <MenuItem
            key={item.value}
            disabled={selectedIdx === idx || disabled?.[item.value]}
            selected={idx === selectedIdx}
            onClick={() => {
              setSelectedIdx(idx);
              setAnchorEl(null);
            }}
          >
            {item.label}
          </MenuItem>
        ))}
      </Menu>
    </Box>
  );
}

export default React.memo(KlineDataSelector);
