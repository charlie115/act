import React, { useEffect, useMemo, useState } from 'react';

import Box from '@mui/material/Box';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormGroup from '@mui/material/FormGroup';
import Stack from '@mui/material/Stack';
import Switch from '@mui/material/Switch';

import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import { useDispatch, useSelector } from 'react-redux';
import { useTranslation } from 'react-i18next';

import { togglePriceView } from 'redux/reducers/home';

import { useDebounce, useVisibilityChange } from '@uidotdev/usehooks';

import { DateTime } from 'luxon';

import isKoreanMarket from 'utils/isKoreanMarket';

import AssetSearchInput from 'components/AssetSearchInput';
import MarketCodeMenu from 'components/MarketCodeMenu';
import PremiumTable from 'components/tables/premium/PremiumTable';

function Home() {
  const { t } = useTranslation();

  const theme = useTheme();

  const isFocused = useVisibilityChange();

  const { timezone } = useSelector((state) => state.app);
  const { loggedin } = useSelector((state) => state.auth);

  const dispatch = useDispatch();

  const [marketCodes, setMarketCodes] = useState(null);

  const [searchValue, setSearchValue] = useState('');
  const debouncedSearchValue = useDebounce(searchValue, 300);

  const [lastActive, setLastActive] = useState();
  const [queryKey, setQueryKey] = useState(DateTime.now().toMillis());

  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const isTetherPriceView = useSelector(
    (state) => state.home.priceView === 'tether'
  );

  const isKimpExchange =
    isKoreanMarket(marketCodes?.targetMarketCode) &&
    !isKoreanMarket(marketCodes?.originMarketCode);

  useEffect(() => {
    if (!isFocused) setLastActive(DateTime.now().toMillis());
    else if (lastActive) {
      const diff = DateTime.now()
        .diff(DateTime.fromMillis(lastActive), ['minutes'])
        .toObject();
      if (diff.minutes > 60) {
        window.location.reload();
      }
      // else if (diff.minutes > 5) {
      //   setQueryKey(DateTime.now().toMillis());
      // }
    }
  }, [isFocused]);

  const assetSearchProps = useMemo(
    () => ({
      apiOptions: { skip: !marketCodes },
      apiParams: {
        ...marketCodes,
        queryKey,
        interval: '1T',
        component: 'premium-table',
      },
    }),
    [marketCodes, queryKey]
  );

  const renderTetherToggle = () =>
    marketCodes ? (
      <FormGroup
        row
        sx={{
          pointerEvents: isKimpExchange ? undefined : 'none',
          width: { xs: 200, sm: 'auto' },
          mb: { xs: 0.5, sm: 2, md: 1, lg: 0 },
        }}
        className={`animate__animated animate__${
          isKimpExchange ? 'zoomIn' : 'zoomOut'
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
          <AssetSearchInput
            onChange={(value) => setSearchValue(value)}
            {...assetSearchProps}
          />
        </Stack>
        <Box>
          <PremiumTable
            marketCodes={marketCodes}
            searchKeyword={debouncedSearchValue}
            loggedin={loggedin}
            isKimpExchange={isKimpExchange}
            isTetherPriceView={isTetherPriceView}
            isMobile={isMobile}
            timezone={timezone}
            queryKey={queryKey}
            onDisconnected={() => {
              setQueryKey(DateTime.now().toMillis());
            }}
          />
        </Box>
      </Box>
    </Box>
  );
}

export default Home;
