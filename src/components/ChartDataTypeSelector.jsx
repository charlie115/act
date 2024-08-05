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

import isPlainObject from 'lodash/isPlainObject';

import { CHART_DATA_TYPE } from 'constants/lists';

const ToggleBtn = styled(ToggleButton)(() => ({
  fontSize: 11,
  padding: '0 15px',
  textTransform: 'none',
}));

function ChartDataTypeSelector({
  defaultValue,
  disabled,
  isFundingRateValid,
  isKimpExchange,
  isTetherPriceView,
  showAvgFundingRateDiff,
  showFundingRate,
  showFundingRateDiff,
  onChange,
}) {
  const { i18n, t } = useTranslation();

  const [selectedIdx, setSelectedIdx] = useState(
    defaultValue
      ? CHART_DATA_TYPE.findIndex((o) => o.value === defaultValue)
      : null
  );
  const debouncedSelectedIdx = useDebounce(selectedIdx, 250);

  const [chartData, setChartData] = useState([]);

  const [anchorEl, setAnchorEl] = useState(null);

  useEffect(() => {
    if (debouncedSelectedIdx !== null && onChange)
      onChange(CHART_DATA_TYPE[debouncedSelectedIdx].value);
  }, [debouncedSelectedIdx]);

  useEffect(() => {
    setChartData(
      CHART_DATA_TYPE.filter((datum) => {
        if (!showFundingRate && datum.value === 'FR') return false;
        if (!showFundingRateDiff && datum.value === 'FRD') return false;
        if (!showAvgFundingRateDiff && datum.value === 'AFRD') return false;
        return true;
      }).map((datum) => ({
        ...datum,
        label: isKimpExchange
          ? [isTetherPriceView ? datum.getTetherLabel() : datum.getKimpLabel()]
          : datum.getLabel(),
        disabled: datum.value === 'AFRD' && !isFundingRateValid,
      }))
    );
  }, [
    i18n.language,
    isFundingRateValid,
    isKimpExchange,
    isTetherPriceView,
    showFundingRate,
  ]);

  if (chartData.length === 0) return null;

  return (
    <Box>
      <ToggleButtonGroup
        exclusive
        disabled={!isPlainObject(disabled) && disabled}
        value={selectedIdx}
        onChange={(e, newIdx) => {
          e.stopPropagation();
          if (newIdx !== null) setSelectedIdx(newIdx);
        }}
        color="secondary"
        size="small"
        sx={{ display: { xs: 'none', md: 'inline-flex' } }}
      >
        {chartData.map((item, idx) => (
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
        {selectedIdx !== null ? chartData[selectedIdx].label : t('Kline Data')}
      </Button>
      <Menu
        anchorEl={anchorEl}
        open={!!anchorEl}
        onClose={() => setAnchorEl(null)}
        sx={{ display: { xs: 'inline-flex', md: 'none' } }}
      >
        {chartData.map((item, idx) => (
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

export default React.memo(ChartDataTypeSelector);
