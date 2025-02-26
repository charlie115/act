import React, { useEffect, useMemo, useState } from 'react';

import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Tooltip from '@mui/material/Tooltip';
import Button from '@mui/material/Button';

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

import { useGetExchangeStatusesQuery } from 'redux/api/drf/exchangestatus';
import { MARKET_CODE_LIST } from 'constants/lists'; // Import the market code list

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
    }
  }, [isFocused, lastActive]);

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
      <Tooltip title={t('View Tether conversion')}>
        <Button
          variant={isTetherPriceView ? "contained" : "outlined"}
          color="info"
          size="small"
          onClick={() => dispatch(togglePriceView(isTetherPriceView ? 'gimp' : 'tether'))}
          disabled={!isKimpExchange}
          sx={{
            minWidth: { xs: '40px', sm: '60px' },
            height: { xs: '28px', sm: '32px' },
            p: { xs: '2px 0px', sm: '4px 8px' },
            borderRadius: '5px',
            textTransform: 'none',
            opacity: isKimpExchange ? 1 : 0.5,
            boxShadow: isTetherPriceView ? '0 2px 5px rgba(0, 150, 255, 0.3)' : 'none',
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              boxShadow: '0 3px 8px rgba(0, 150, 255, 0.4)',
              transform: 'translateY(-1px)',
            },
            position: 'relative',
            overflow: 'hidden',
            '&::before': isTetherPriceView ? {
              content: '""',
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'linear-gradient(45deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 100%)',
              zIndex: 1,
            } : {},
          }}
        >
          <Box
            component="span"
            sx={{
              fontSize: { xs: '0.8rem', sm: '0.9rem' },
              fontWeight: 600,
              letterSpacing: '0.02em',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            %/₮
          </Box>
        </Button>
      </Tooltip>
    ) : null;

  const { data: exchangeStatuses = [] } = useGetExchangeStatusesQuery();

  // Check server_check for originMarketCode and targetMarketCode
  const maintenanceInfo = useMemo(() => {
    if (!marketCodes) return null;

    const originStatus = exchangeStatuses.find(
      (record) => record.market_code === marketCodes.originMarketCode
    );
    const targetStatus = exchangeStatuses.find(
      (record) => record.market_code === marketCodes.targetMarketCode
    );

    const originCheck = originStatus?.server_check === true;
    const targetCheck = targetStatus?.server_check === true;

    if (originCheck) return { ...originStatus, code: marketCodes.originMarketCode };
    if (targetCheck) return { ...targetStatus, code: marketCodes.targetMarketCode };

    return null;
  }, [marketCodes, exchangeStatuses]);

  // Find the market code object from MARKET_CODE_LIST to get its icon
  const maintenanceMarket = useMemo(() => {
    if (!maintenanceInfo) return null;
    return MARKET_CODE_LIST.find((m) => m.value === maintenanceInfo.code) || null;
  }, [maintenanceInfo]);

  return (
    <Box sx={{ overflowX: 'hidden', mb: 2, p: 1 }}>
      <Box>
        <Stack
          direction="row"
          justifyContent="space-between"
          spacing={{ xs: 1, sm: 0 }}
          sx={{ mb: 2 }}
          alignItems="center"
        >
          <MarketCodeMenu onChange={(value) => setMarketCodes(value)} />
          <Stack 
            direction="row" 
            alignItems="center"
            spacing={1}
          >
            {renderTetherToggle()}
            <AssetSearchInput
              onChange={(value) => setSearchValue(value)}
              {...assetSearchProps}
              sx={{
                '& .MuiInputBase-root': {
                  height: { xs: '26px', sm: 'auto' },
                },
                '& .MuiOutlinedInput-input': {
                  padding: { xs: '4px 8px', sm: '8px 14px' },
                  fontSize: { xs: '0.8rem', sm: '1rem' },
                },
              }}
            />
          </Stack>
        </Stack>

        {maintenanceInfo && maintenanceMarket && (
          <Box
            sx={{
              mb: 2,
              p: 2,
              border: '1px solid',
              borderColor: 'warning.main',
              borderRadius: 1,
              backgroundColor: 'warning.lighter',
              display: 'flex',
              alignItems: 'center',
              gap: 1,
            }}
          >
            <Box
              component="img"
              src={maintenanceMarket.icon}
              alt={maintenanceMarket.getLabel()}
              sx={{ width: 30, height: 30 }}
            />
            <Typography variant="body1" color="warning.dark" fontWeight={600}>
              {t('Server Maintenance is in progress')}
            </Typography>
          </Box>
        )}

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