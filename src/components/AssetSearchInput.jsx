import React, {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from 'react';

import Autocomplete, { autocompleteClasses } from '@mui/material/Autocomplete';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';
import LinearProgress from '@mui/material/LinearProgress';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';

import BlockIcon from '@mui/icons-material/Block';
import DoneIcon from '@mui/icons-material/Done';
import SearchIcon from '@mui/icons-material/Search';

import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import { useTranslation } from 'react-i18next';

import { useGetAssetsQuery } from 'redux/api/drf/infocore';
import { useGetRealTimeKlineQuery } from 'redux/api/websocket/kline';

import { useDebounce } from '@uidotdev/usehooks';

const AssetSearchInput = forwardRef(
  (
    {
      apiOptions,
      apiParams,
      customList,
      onChange,
      onSelect,
      selectIcon,
      showSelect,
    },
    ref
  ) => {
    const inputRef = useRef();
    const { t } = useTranslation();

    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('md'));

    const [open, setOpen] = React.useState(false);
    const [options, setOptions] = useState([]);

    const [selected, setSelected] = useState('');

    const [searchValue, setSearchValue] = useState('');
    const debouncedSearchValue = useDebounce(searchValue, 500);

    useImperativeHandle(
      ref,
      () => ({
        open: () => setOpen(true),
      }),
      []
    );

    const realTimeKlineOptions = useMemo(() => {
      if (customList) return { ...apiOptions, skip: true };
      return apiOptions;
    }, [apiOptions, customList]);

    const { data: assetsData } = useGetAssetsQuery();
    const { currentData, isFetching } = useGetRealTimeKlineQuery(
      apiParams,
      realTimeKlineOptions
    );

    const assets = useMemo(() => {
      if (!currentData?.disconnected)
        return Object.keys(currentData ?? {})
          .sort()
          .join();
      return '';
    }, [currentData]);

    useEffect(() => {
      if (customList) setOptions(customList.sort());
      else if (assets) setOptions(assets.split(','));
      else setOptions([]);
    }, [assets, customList]);

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
              InputLabelProps={{
                sx: { fontSize: isMobile ? '0.875rem !important' : undefined }
              }}
              InputProps={{
                ...params.InputProps,
                sx: {
                  ...params.InputProps.sx,
                  '& input': {
                    fontSize: isMobile ? '0.875rem !important' : '1rem',
                  }
                },
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon sx={{ fontSize: isMobile ? '1rem' : '1.25rem' }} />
                  </InputAdornment>
                ),
              }}
            />
            {isFetching && options.length === 0 && <LinearProgress />}
          </>
        )}
        renderOption={(props, option) => (
          <Box
            {...props}
            component="li"
            sx={{
              '& .asset-icon': { mr: 1, flexShrink: 0 },
              [`&.${autocompleteClasses.option}`]: {
                px: 1,
                py: isMobile ? 0.75 : 0.5,
                pr: 0,
                '& > p': { fontSize: isMobile ? '1rem' : '1rem' },
              },
            }}
          >
            {assetsData?.[option]?.icon ? (
              <img
                className="asset-icon"
                width={isMobile ? 14 : 12}
                src={assetsData[option].icon}
                alt=""
              />
            ) : (
              <BlockIcon
                className="asset-icon"
                color="secondary"
                sx={{ fontSize: isMobile ? 14 : 12 }}
              />
            )}
            <Typography sx={{ mr: 'auto' }}>{option}</Typography>
            {showSelect && (
              <IconButton
                onClick={(e) => {
                  e.stopPropagation();
                  onSelect(option);
                  setSelected(option);
                  setOpen(false);
                  inputRef.current?.blur();
                }}
                sx={{ alignSelf: 'flex-end', p: 0 }}
              >
                {selectIcon || <DoneIcon />}
              </IconButton>
            )}
          </Box>
        )}
        sx={{ 
          width: isMobile ? 120 : 215,
          '& .MuiInputBase-root': {
            height: isMobile ? 40 : undefined
          }
        }}
      />
    );
  }
);

export default AssetSearchInput;
