import React, { useCallback, useEffect, useState } from 'react';

import Box from '@mui/material/Box';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormGroup from '@mui/material/FormGroup';
import InputAdornment from '@mui/material/InputAdornment';
import OutlinedInput from '@mui/material/OutlinedInput';
import Stack from '@mui/material/Stack';
import Switch from '@mui/material/Switch';

import CloseIcon from '@mui/icons-material/Close';
import SearchIcon from '@mui/icons-material/Search';

import useMediaQuery from '@mui/material/useMediaQuery';

import { useTheme } from '@mui/material/styles';

import { useDispatch, useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';

import { togglePriceView } from 'redux/reducers/home';

import debounce from 'lodash/debounce';

import isKoreanMarket from 'utils/isKoreanMarket';

import MarketCodeMenu from 'components/MarketCodeMenu';
import PremiumTable from 'components/premium_table/PremiumTable';

function Home() {
  const { t } = useTranslation();

  const theme = useTheme();

  const { timezone } = useSelector((state) => state.app);
  const { loggedin } = useSelector((state) => state.auth);

  const dispatch = useDispatch();

  const [marketCodes, setMarketCodes] = useState(null);

  const [searchKeyword, setSearchKeyword] = useState('');
  const [searchValue, setSearchValue] = useState('');

  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const isSmallScreen = useMediaQuery('(max-width:420px)');

  const isTetherPriceView = useSelector(
    (state) => state.home.priceView === 'tether'
  );

  const isKimpExchange =
    isKoreanMarket(marketCodes?.targetMarketCode) &&
    !isKoreanMarket(marketCodes?.originMarketCode);

  const onChange = (value) => setSearchKeyword(value);
  const debouncedOnChange = useCallback(
    debounce(onChange, 500, { leading: false, trailing: true })
  );

  useEffect(() => {
    debouncedOnChange(searchValue);
  }, [searchValue]);

  const renderTetherToggle = () =>
    marketCodes ? (
      <FormGroup
        row
        sx={{
          pointerEvents:
            isKoreanMarket(marketCodes?.targetMarketCode) &&
            !isKoreanMarket(marketCodes?.originMarketCode)
              ? undefined
              : 'none',
          width: { xs: 200, sm: 'auto' },
          mb: { xs: 0.5, sm: 2, md: 1, lg: 0 },
        }}
        className={`animate__animated animate__${
          isKoreanMarket(marketCodes?.targetMarketCode) &&
          !isKoreanMarket(marketCodes?.originMarketCode)
            ? 'zoomIn'
            : 'zoomOut'
        }`}
      >
        <FormControlLabel
          checked={isTetherPriceView}
          control={
            <Switch
              color="info"
              size={isMobile ? 'small' : 'medium'}
              checked={isTetherPriceView}
              onChange={(e) =>
                dispatch(togglePriceView(e.target.checked ? 'tether' : 'gimp'))
              }
            />
          }
          label={t('View Tether conversion')}
          labelPlacement="start"
          slotProps={{
            typography: {
              sx: {
                color: isTetherPriceView ? 'info.main' : 'inherit',
                fontSize: { xs: '0.65rem', sm: '0.8rem' },
                fontWeight: 700,
              },
            },
          }}
          sx={{ ml: { xs: 0.5, sm: 1 } }}
        />
      </FormGroup>
    ) : null;

  return (
    <Box sx={{ overflowX: 'hidden', mb: 2, p: 1 }}>
      <Box>
        {renderTetherToggle()}
        <Stack
          direction="row"
          justifyContent="space-between"
          spacing={{ xs: 1, sm: 0 }}
          sx={{ mb: 2 }}
        >
          <MarketCodeMenu onChange={(value) => setMarketCodes(value)} />
          <OutlinedInput
            size="small"
            placeholder={t('Search')}
            onChange={(e) => setSearchValue(e.target.value)}
            value={searchValue}
            startAdornment={
              <InputAdornment position="start">
                <SearchIcon sx={isMobile ? { fontSize: '1em' } : {}} />
              </InputAdornment>
            }
            endAdornment={
              <InputAdornment
                position="end"
                sx={{ cursor: 'pointer', ':hover': { opacity: 0.5 } }}
              >
                <CloseIcon
                  onClick={() => {
                    setSearchKeyword('');
                    setSearchValue('');
                  }}
                  sx={isMobile ? { fontSize: '1em' } : {}}
                />
              </InputAdornment>
            }
            inputProps={{
              style: isSmallScreen ? { height: '0.5em', width: 60 } : {},
            }}
            sx={{
              '& .MuiInputBase-root': { px: { xs: 0.5, sm: 1 } },
            }}
          />
        </Stack>
        <Box>
          <PremiumTable
            marketCodes={marketCodes}
            searchKeyword={searchKeyword}
            loggedin={loggedin}
            isKimpExchange={isKimpExchange}
            isTetherPriceView={isTetherPriceView}
            isMobile={isMobile}
            timezone={timezone}
          />
        </Box>
      </Box>
    </Box>
  );
}

export default Home;
