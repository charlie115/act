import React, { useCallback, useEffect, useState } from 'react';

import Autocomplete from '@mui/material/Autocomplete';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';

import BlockIcon from '@mui/icons-material/Block';
import SearchOutlinedIcon from '@mui/icons-material/SearchOutlined';

import { alpha, useTheme } from '@mui/material/styles';

import debounce from 'lodash/debounce';
import { matchSorter } from 'match-sorter';

import { useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';

import { coinicons } from 'assets/exports';

export default function CoinsSelector({ onChange }) {
  const { t } = useTranslation();
  const theme = useTheme();

  const [open, setOpen] = useState(false);
  const [options, setOptions] = useState([]);
  const [selected, setSelected] = useState([]);

  const coins = useSelector((state) => state.websocket.coins);

  useEffect(() => {
    setOptions(coins.map((coin) => ({ name: coin })));
  }, [coins]);

  const onInputChange = (newInput) => {
    if (selected.length === 0)
      onChange(
        matchSorter(coins, newInput, {
          maxRanking: matchSorter.rankings.STARTS_WITH,
        })
      );
  };
  const debouncedOnInputChange = useCallback(debounce(onInputChange, 500));

  const onValueChange = (newValue) => onChange(newValue.map((val) => val.name));
  const debouncedOnValueChange = useCallback(debounce(onValueChange, 500), []);

  return (
    <Stack
      useFlexGap
      direction="row"
      flexWrap="wrap"
      spacing={1}
      sx={{ alignItems: 'center' }}
    >
      {options.length > 0 && (
        <Typography color="secondary" sx={{ fontStyle: 'italic' }}>
          {t('Total {{value}} cryptocurrencies', { value: options.length })}
        </Typography>
      )}
      <Autocomplete
        disableCloseOnSelect
        multiple
        clearOnBlur={false}
        id="coins-selector"
        open={open}
        onOpen={() => setOpen(true)}
        onClose={() => setOpen(false)}
        onChange={(e, newValue) => {
          setSelected(newValue);
          debouncedOnValueChange(newValue);
        }}
        onInputChange={(e, newInput) => debouncedOnInputChange(newInput)}
        isOptionEqualToValue={(option, value) => option.name === value.name}
        getOptionLabel={(option) => option.name}
        options={options}
        noOptionsText={t('Coin does not exist')}
        loading={coins.length === 0}
        limitTags={2}
        renderInput={(params) => (
          <TextField
            {...params}
            color="secondary"
            variant="outlined"
            label={t('Search coins')}
            InputProps={params.InputProps}
          />
        )}
        renderOption={(props, option) => (
          <Box
            component="li"
            sx={{ '& > img': { mr: 2, flexShrink: 0 } }}
            {...props}
          >
            {coinicons[`${option.name}.png`] ? (
              <img
                loading="lazy"
                width="20"
                src={require(`assets/icons/coinicon/${option.name}.png`)}
                alt=""
              />
            ) : (
              <BlockIcon color="secondary" sx={{ fontSize: 20, mr: 2 }} />
            )}
            {option.name}
          </Box>
        )}
        ListboxProps={{
          sx: { bgcolor: alpha(theme.palette.background.default, 0.15) },
        }}
        popupIcon={<SearchOutlinedIcon color="secondary" fontSize="small" />}
        size="small"
        sx={{
          height: 40,
          width: 240,
          '& .MuiAutocomplete-popupIndicator': { transform: 'none' },
          '& .MuiAutocomplete-input': { textTransform: 'uppercase' },
          '& .MuiFormControl-root': {
            bgcolor: open ? alpha(theme.palette.background.default, 0.5) : null,
            '& .MuiInputBase-root': { pr: '20px!important' },
          },
        }}
      />
    </Stack>
  );
}
