import React, { useEffect, useMemo, useRef, useState } from 'react';

import {
  Link,
  Navigate,
  Outlet,
  useLocation,
  useNavigate,
} from 'react-router-dom';

import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import IconButton from '@mui/material/IconButton';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import Stack from '@mui/material/Stack';

import AddIcon from '@mui/icons-material/Add';
import CheckBoxIcon from '@mui/icons-material/CheckBox';

import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import {
  useGetNodesQuery,
  usePostTradeConfigMutation,
} from 'redux/api/drf/tradecore';

import { useSelector } from 'react-redux';

import { useTranslation } from 'react-i18next';
import i18n from 'configs/i18n';

import { useVisibilityChange } from '@uidotdev/usehooks';

import { DateTime } from 'luxon';

import sortBy from 'lodash/sortBy';
import uniqBy from 'lodash/uniqBy';

import a11yProps from 'utils/a11yProps';

import MarketCodeCombinationSelector from 'components/MarketCodeCombinationSelector';
import TelegramLoginButton from 'components/TelegramLoginButton';

import { MARKET_CODE_LIST } from 'constants/lists';

const TAB = {
  triggers: '/bot/triggers',
  position: '/bot/position',
  capital: '/bot/capital',
  pnlHistory: '/bot/pnl-history',
  botSettings: '/bot/settings',
  apiKey: '/bot/api-key',
  deposit: '/bot/deposit',
  userGuide: '/community-board/',
  supportCenter: 8,
};

const TABS = [
  {
    id: TAB.triggers,
    name: '/bot/triggers',
    getLabel: () => i18n.t('Triggers'),
  },
  {
    id: TAB.position,
    name: '/bot/position',
    getLabel: () => i18n.t('Position'),
  },
  {
    id: TAB.capital,
    name: '/bot/capital',
    getLabel: () => i18n.t('Capital'),
  },
  {
    id: TAB.pnlHistory,
    name: '/bot/pnl-history',
    getLabel: () => i18n.t('PnL History'),
  },
  {
    id: TAB.botSettings,
    name: '/bot/settings',
    getLabel: () => i18n.t('BOT Settings'),
  },
  {
    id: TAB.apiKey,
    name: '/bot/api-key',
    getLabel: () => i18n.t('API Key Settings'),
  },
  {
    id: TAB.deposit,
    name: '/bot/deposit',
    getLabel: () => i18n.t('Deposit/Withdrawal'),
  },
  {
    id: TAB.userGuide,
    name: '/community-board/',
    getLabel: () => i18n.t('User Guide'),
    component: Box,
  },
  // {
  //   id: TAB.supportCenter,
  //   name: 'supportCenter',
  //   getLabel: () => i18n.t('Support Center'),
  //   component: Box,
  //   disabled: true,
  // },
];

const MARKET_CODES_REQUIRED = [TAB.botSettings, TAB.position, TAB.capital];
const TRADE_SUPPORT_REQUIRED = [TAB.position, TAB.capital, TAB.pnlHistory, TAB.apiKey];

export default function Bot() {
  const marketCodeSelectorRef = useRef();

  const { t } = useTranslation();

  const isFocused = useVisibilityChange();

  const theme = useTheme();
  const location = useLocation();
  const navigate = useNavigate();

  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const { loggedin, user } = useSelector((state) => state.auth);

  const { data: nodes } = useGetNodesQuery();

  const tradeConfigAllocations = useMemo(
    () =>
      user?.trade_config_allocations?.map((tradeConfig) => {
        const target = MARKET_CODE_LIST.find(
          (o) => o.value === tradeConfig.target_market_code
        );
        const origin = MARKET_CODE_LIST.find(
          (o) => o.value === tradeConfig.origin_market_code
        );
        const node = tradeConfig?.node;
        return {
          node,
          target,
          origin,
          uuid: tradeConfig.trade_config_uuid,
          value: `${tradeConfig.target_market_code}:${tradeConfig.origin_market_code}`,
        };
      }) || [],
    [user?.trade_config_allocations]
  );

  const tradeConfigUuids = useMemo(
    () => user?.trade_config_allocations?.map((o) => o.trade_config_uuid) || [],
    [user?.trade_config_allocations]
  );

  const [lastActive, setLastActive] = useState();
  const [queryKey, setQueryKey] = useState(DateTime.now().toMillis());

  const [marketCodeCombinationList, setMarketCodeCombinationList] = useState(
    []
  );
  const [selectedMarketCodeCombination, setSelectedMarketCodeCombination] =
    useState();
  const [postTradeConfig, tradeConfigResults] = usePostTradeConfigMutation();

  const [showTelegramDialog, setShowTelegramDialog] = useState(false);

  useEffect(() => {
    if (nodes?.results?.length > 0) {
      const nodeMarketCodes = nodes.results.reduce(
        (acc, curr) =>
          acc.concat(
            curr.market_code_combinations?.map((item) => ({
              marketCodeCombination: item.market_code_combination,
              tradeSupport: item.trade_support,
              ...curr,
            }))
          ),
        []
      );
      const uniqNodeMarketCodes = uniqBy(
        nodeMarketCodes,
        'marketCodeCombination'
      );
      const marketCodes = [
        {
          label: t('All'),
          getLabel: () => i18n.t('All'),
          value: 'ALL',
          icon: <CheckBoxIcon sx={{ verticalAlign: 'middle' }} />,
        },
      ].concat(
        sortBy(
          uniqNodeMarketCodes.map((item) => {
            const [targetMarket, originMarket] =
              item.marketCodeCombination.split(':');
            const target = MARKET_CODE_LIST.find(
              (o) => o.value === targetMarket
            );
            const origin = MARKET_CODE_LIST.find(
              (o) => o.value === originMarket
            );
            const tradeConfigAllocation = user?.trade_config_allocations?.find(
              (tradeConfig) =>
                tradeConfig.target_market_code === targetMarket &&
                tradeConfig.origin_market_code === originMarket
            );
            return {
              ...item,
              disabled:
                !tradeConfigAllocation?.trade_config_uuid ||
                (MARKET_CODES_REQUIRED.includes(location.pathname) &&
                  !selectedMarketCodeCombination) ||
                (TRADE_SUPPORT_REQUIRED.includes(location.pathname) &&
                  !item.tradeSupport),
              target: {
                ...target,
                isSpot: targetMarket.includes('SPOT'),
                icon: (
                  <Box
                    component="img"
                    src={target.icon}
                    alt={target.getLabel()}
                    sx={{
                      height: { xs: 16, md: 18 },
                      width: { xs: 16, md: 18 },
                      verticalAlign: 'middle',
                    }}
                  />
                ),
              },
              origin: {
                ...origin,
                isSpot: originMarket.includes('SPOT'),
                icon: (
                  <Box
                    component="img"
                    src={origin.icon}
                    alt={origin.getLabel()}
                    sx={{
                      height: { xs: 16, md: 18 },
                      width: { xs: 16, md: 18 },
                      verticalAlign: 'middle',
                    }}
                  />
                ),
              },
              secondaryIcon: !tradeConfigAllocation?.trade_config_uuid ? (
                <IconButton
                  color="success"
                  edge="end"
                  onClick={(e) => {
                    e.stopPropagation();
                    postTradeConfig({
                      acw_user_uuid: user?.uuid,
                      target_market_code: target.value,
                      origin_market_code: origin.value,
                    });
                  }}
                  sx={{ p: 0 }}
                >
                  <AddIcon sx={{ fontSize: 20 }} />
                </IconButton>
              ) : null,
              tradeConfigUuid: tradeConfigAllocation?.trade_config_uuid,
              value: item.marketCodeCombination,
            };
          }),
          'tradeConfigUuid'
        )
      );
      setMarketCodeCombinationList(marketCodes);
      if (!selectedMarketCodeCombination) {
        if (location.state?.marketCodeCombination) {
          setSelectedMarketCodeCombination(
            marketCodes.find(
              (o) => o.value === location.state.marketCodeCombination
            )
          );
        } else setSelectedMarketCodeCombination(marketCodes[0]);
      } else if (
        selectedMarketCodeCombination.value !== 'ALL' &&
        !selectedMarketCodeCombination.tradeConfigUuid
      ) {
        const tradeConfigAllocation = user?.trade_config_allocations?.find(
          (tradeConfig) =>
            tradeConfig.target_market_code ===
              selectedMarketCodeCombination.target.value &&
            tradeConfig.origin_market_code ===
              selectedMarketCodeCombination.origin.value
        );
        if (tradeConfigAllocation)
          setSelectedMarketCodeCombination((state) => ({
            ...state,
            tradeConfigUuid: tradeConfigAllocation.trade_config_uuid,
          }));
      }
    }
  }, [
    location.pathname,
    location.state,
    nodes,
    selectedMarketCodeCombination,
    user,
  ]);

  useEffect(() => {
    if (!isFocused) setLastActive(DateTime.now().toMillis());
    else if (lastActive) {
      const diff = DateTime.now()
        .diff(DateTime.fromMillis(lastActive), ['minutes'])
        .toObject();
      if (diff.minutes > 60) {
        window.location.reload();
      } else if (diff.minutes > 1) {
        setQueryKey(DateTime.now().toMillis());
      }
    }
  }, [isFocused]);

  useEffect(() => {
    if (
      MARKET_CODES_REQUIRED.includes(location.pathname) &&
      ((!selectedMarketCodeCombination &&
        !location.state?.marketCodeCombination) ||
        selectedMarketCodeCombination?.value === 'ALL')
    )
      marketCodeSelectorRef?.current?.open();
  }, [location.pathname, location.state, selectedMarketCodeCombination]);

  useEffect(() => {
    if (
      TRADE_SUPPORT_REQUIRED.includes(location.pathname) &&
      !location.state?.marketCodeCombination &&
      !selectedMarketCodeCombination?.tradeSupport
    ) {
      marketCodeSelectorRef?.current?.open();
    }
  }, [location.pathname, location.state, selectedMarketCodeCombination]);

  useEffect(() => {
    if (loggedin && !user?.telegram_chat_id) {
      setShowTelegramDialog(true);
    }
  }, [loggedin, user?.telegram_chat_id]);

  useEffect(() => () => window.history.replaceState(null, ''), []);

  if (!loggedin)
    return <Navigate replace to="/login" state={{ from: location }} />;

  return (
    <>
      <Dialog
        open={showTelegramDialog}
        onClose={() => setShowTelegramDialog(false)}
      >
        <DialogTitle>{t('Connect to Telegram')}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ py: 2 }}>
            <DialogContentText>
              {t('Please connect your Telegram account to continue using the bot features')}
            </DialogContentText>
            <TelegramLoginButton buttonId="telegram-bot-page-button" />
          </Stack>
        </DialogContent>
      </Dialog>

      <Box sx={{ flex: 1, overflowX: 'hidden' }}>
        <Box sx={isMobile ? { maxWidth: window.innerWidth * 0.95 } : {}}>
          <Grid container sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Grid item md xs={12}>
              {location.pathname === '/bot' ? (
                <Box />
              ) : (
                <Tabs
                  allowScrollButtonsMobile
                  scrollButtons
                  aria-label="arbitrage-tabs"
                  variant="scrollable"
                  value={location.pathname}
                  // value={currentTab}
                  // onChange={(e, newValue) => setCurrentTab(newValue)}
                  sx={{ borderBottom: 0, mb: 0 }}
                >
                  {TABS.map(({ id, name, disabled, getLabel }) => {
                    let state;
                    if (name === '/community-board/') {
                      // pass state with category 'User Guide'
                      state = { category: 'User Guide' };
                    } else {
                      state = {
                        marketCodeCombination: selectedMarketCodeCombination?.value,
                      };
                    }

                    return (
                      <Tab
                        component={Link}
                        key={name}
                        label={getLabel()}
                        value={name}
                        to={name}
                        state={state}
                        disabled={
                          disabled ||
                          (TRADE_SUPPORT_REQUIRED.includes(name) &&
                            !selectedMarketCodeCombination?.tradeSupport)
                        }
                        {...a11yProps({ id, name })}
                      />
                    );
                  })}
                </Tabs>
              )}
            </Grid>
            <Grid
              item
              md
              xs={12}
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: { xs: 'center', md: 'flex-end' },
                my: { xs: 1, md: 0 },
              }}
            >
              <MarketCodeCombinationSelector
                ref={marketCodeSelectorRef}
                options={marketCodeCombinationList}
                value={selectedMarketCodeCombination}
                loading={tradeConfigResults.isLoading}
                marketCodesRequired={MARKET_CODES_REQUIRED.includes(
                  location.pathname
                )}
                tradeSupportRequired={TRADE_SUPPORT_REQUIRED.includes(
                  location.pathname
                )}
                onSelectItem={(newValue) => {
                  if (
                    (MARKET_CODES_REQUIRED.includes(location.pathname) ||
                      TRADE_SUPPORT_REQUIRED.includes(location.pathname)) &&
                    newValue.value === 'ALL'
                  )
                    navigate('/bot');
                  setSelectedMarketCodeCombination(newValue);
                }}
              />
            </Grid>
          </Grid>
        </Box>
        <Box sx={{ overflowX: 'hidden', mb: 2, p: 1 }}>
          {!selectedMarketCodeCombination ||
          (MARKET_CODES_REQUIRED.includes(location.pathname) &&
            selectedMarketCodeCombination.value === 'ALL') ? (
            <Box />
          ) : (
            <Outlet
              context={{
                marketCodeSelectorRef,
                queryKey,
                tradeConfigAllocations,
                tradeConfigUuids,
                marketCodeCombination: selectedMarketCodeCombination,
              }}
            />
          )}
        </Box>
        {/* <SwipeableViews
          axis={theme.direction === 'rtl' ? 'x-reverse' : 'x'}
          index={currentTab}
          onChangeIndex={(newIndex) => setCurrentTab(newIndex)}
          >
          {TABS.map(({ id, name, ...others }) => (
            <TabPanel
              key={name}
              id={name}
              index={id}
              dir={theme.direction}
              value={currentTab}
            >
              {currentTab === id && (
                <Box sx={{ overflowX: 'hidden', mb: 2, p: 1 }}>
                  {!selectedMarketCodeCombination ||
                  (MARKET_CODES_REQUIRED.includes(currentTab) &&
                    selectedMarketCodeCombination.value === 'ALL') ? (
                    <LinearProgress />
                  ) : (
                    <others.component
                      marketCodeSelectorRef={marketCodeSelectorRef}
                      marketCodeCombination={selectedMarketCodeCombination}
                      queryKey={queryKey}
                      tradeConfigAllocations={tradeConfigAllocations}
                      tradeConfigUuids={tradeConfigUuids}
                      onChangeTabHandler={(newTab) => setCurrentTab(newTab)}
                    />
                  )}
                </Box>
              )}
            </TabPanel>
          ))}
        </SwipeableViews> */}
      </Box>
    </>
  );
}
