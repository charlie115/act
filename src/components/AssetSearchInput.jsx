import React, { useEffect, useMemo, useRef, useState } from 'react';

import Autocomplete from '@mui/material/Autocomplete';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';
import LinearProgress from '@mui/material/LinearProgress';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';

import AddIcon from '@mui/icons-material/Add';
import BlockIcon from '@mui/icons-material/Block';
import SearchIcon from '@mui/icons-material/Search';

import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import { useTranslation } from 'react-i18next';

import { useGetAssetsQuery } from 'redux/api/drf/infocore';
import { useGetRealTimeKlineQuery } from 'redux/api/websocket/kline';

import { useDebounce } from '@uidotdev/usehooks';

export default function AssetSearchInput({
  apiOptions,
  apiParams,
  onChange,
  onSelect,
}) {
  const inputRef = useRef();
  const { t } = useTranslation();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [open, setOpen] = React.useState(false);
  const [options, setOptions] = useState([]);

  const [selected, setSelected] = useState('');

  const [searchValue, setSearchValue] = useState('');
  const debouncedSearchValue = useDebounce(searchValue, 500);

  const { data: assetsData } = useGetAssetsQuery();
  const { data, isFetching } = useGetRealTimeKlineQuery(apiParams, apiOptions);

  const assets = useMemo(
    () =>
      Object.keys(data ?? {})
        .sort()
        .join(),
    [data]
  );

  useEffect(() => {
    if (assets) setOptions(assets.split(','));
    else setOptions([]);
  }, [assets]);

  useEffect(() => {
    onChange(debouncedSearchValue);
  }, [debouncedSearchValue]);

  return (
    <Autocomplete
      autoHighlight
      freeSolo
      id="asset-search-input"
      size="small"
      options={options}
      loading={options.length === 0 && isFetching}
      isOptionEqualToValue={(option, value) =>
        option.toLowerCase() === value.toLowerCase()
      }
      getOptionLabel={(option) => option}
      open={open}
      onOpen={() => {
        setOpen(true);
      }}
      onClose={() => {
        setOpen(false);
      }}
      inputValue={searchValue}
      value={selected}
      onChange={(event, newValue) => {
        onChange(newValue);
        if (onSelect && !newValue) {
          setSelected('');
          onSelect('');
        }
      }}
      onInputChange={(event, newValue) => setSearchValue(newValue)}
      renderInput={(params) => (
        <>
          <TextField
            {...params}
            inputRef={inputRef}
            label={t('Search')}
            InputProps={{
              ...params.InputProps,
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon sx={isMobile ? { fontSize: '0.8em' } : {}} />
                </InputAdornment>
              ),
            }}
          />
          {isFetching && options.length === 0 && <LinearProgress />}
        </>
      )}
      renderOption={(props, option) => (
        <Box
          component="li"
          sx={{
            '& > img': { mr: 2, flexShrink: 0 },
            '& > svg': { mr: 2, flexShrink: 0 },
          }}
          {...props}
        >
          {assetsData?.[option]?.icon ? (
            <img width="12" src={assetsData[option].icon} alt="" />
          ) : (
            <BlockIcon color="secondary" sx={{ fontSize: 12 }} />
          )}
          <Typography sx={{ mr: 'auto' }}>{option}</Typography>
          <IconButton
            onClick={(e) => {
              e.stopPropagation();
              onSelect(option);
              setSelected(option);
              setOpen(false);
              inputRef.current?.blur();
            }}
          >
            <AddIcon />
          </IconButton>
        </Box>
      )}
      sx={{ width: 215 }}
    />
  );
}
