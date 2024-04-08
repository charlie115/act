import React, { useEffect, useMemo, useRef, useState } from 'react';

import { Navigate, useLocation } from 'react-router-dom';

import SwipeableViews from 'react-swipeable-views';

import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import IconButton from '@mui/material/IconButton';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';

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

import TabPanel from 'components/TabPanel';

import APIKeySettings from 'components/APIKeySettings';
import BotSettings from 'components/BotSettings';
import MarketCodeCombinationSelector from 'components/MarketCodeCombinationSelector';
import PnLHistory from 'components/PnLHistory';
import PositionTable from 'components/tables/position/PositionTable';
import TriggersTable from 'components/tables/trigger/TriggersTable';

import { MARKET_CODE_LIST } from 'constants/lists';

const TAB = {
  triggers: 0,
  position: 1,
  pnlHistory: 2,
  botSettings: 3,
  apiKeySettings: 4,
  userGuide: 5,
  supportCenter: 6,
};

const TABS = [
  {
    id: TAB.triggers,
    name: 'triggers',
    getLabel: () => i18n.t('Triggers'),
    component: TriggersTable,
  },
  {
    id: TAB.position,
    name: 'position',
    getLabel: () => i18n.t('Position'),
    component: PositionTable,
  },
  {
    id: TAB.pnlHistory,
    name: 'pnlHistory',
    getLabel: () => i18n.t('PnL History'),
    component: PnLHistory,
  },
  {
    id: TAB.botSettings,
    name: 'botSettings',
    getLabel: () => i18n.t('BOT Settings'),
    component: BotSettings,
  },
  {
    id: TAB.apiKeySettings,
    name: 'apiKeySettings',
    getLabel: () => i18n.t('API Key Settings'),
    component: APIKeySettings,
  },
  {
    id: TAB.userGuide,
    name: 'userGuide',
    getLabel: () => i18n.t('User Guide'),
    component: Box,
  },
  {
    id: TAB.supportCenter,
    name: 'supportCenter',
    getLabel: () => i18n.t('Support Center'),
    component: Box,
  },
];

const MARKET_CODES_REQUIRED = [TAB.position];
const TRADE_SUPPORT_REQUIRED = [TAB.pnlHistory, TAB.apiKeySettings];

export default function Bot() {
  const marketCodeSelectorRef = useRef();

  const { t } = useTranslation();

  const isFocused = useVisibilityChange();

  const theme = useTheme();
  const location = useLocation();

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
        return {
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

  const [currentTab, setCurrentTab] = useState(0);
  const [marketCodeCombinationList, setMarketCodeCombinationList] = useState(
    []
  );
  const [selectedMarketCodeCombination, setSelectedMarketCodeCombination] =
    useState();

  const [postTradeConfig, tradeConfigResults] = usePostTradeConfigMutation();

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
                (MARKET_CODES_REQUIRED.includes(currentTab) &&
                  !selectedMarketCodeCombination) ||
                (TRADE_SUPPORT_REQUIRED.includes(currentTab) &&
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
                  <AddIcon sx={{ fontSize: 16 }} />
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
      if (!selectedMarketCodeCombination)
        setSelectedMarketCodeCombination(marketCodes[0]);
      else if (
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
  }, [nodes, currentTab, selectedMarketCodeCombination, user]);

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

  if (!loggedin)
    return <Navigate replace to="/login" state={{ from: location }} />;

  return (
    <Box sx={{ flex: 1, overflowX: 'hidden' }}>
      <Box sx={isMobile ? { maxWidth: window.innerWidth * 0.95 } : {}}>
        <Grid container sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Grid item md xs={12}>
            <Tabs
              allowScrollButtonsMobile
              scrollButtons
              aria-label="arbitrage-tabs"
              variant="scrollable"
              value={currentTab}
              onChange={(e, newValue) => setCurrentTab(newValue)}
              sx={{ borderBottom: 0, mb: 0 }}
            >
              {TABS.map(({ id, name, getLabel }) => (
                <Tab
                  key={name}
                  label={getLabel()}
                  value={id}
                  disabled={
                    id > TAB.apiKeySettings ||
                    (MARKET_CODES_REQUIRED.includes(id) &&
                      selectedMarketCodeCombination?.value === 'ALL') ||
                    (TRADE_SUPPORT_REQUIRED.includes(id) &&
                      !selectedMarketCodeCombination?.tradeSupport)
                  }
                  {...a11yProps({ id, name })}
                />
              ))}
            </Tabs>
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
              onSelectItem={(newValue) => {
                if (
                  (MARKET_CODES_REQUIRED.includes(currentTab) ||
                    TRADE_SUPPORT_REQUIRED.includes(currentTab)) &&
                  newValue.value === 'ALL'
                )
                  setCurrentTab(0);
                setSelectedMarketCodeCombination(newValue);
              }}
            />
          </Grid>
        </Grid>
      </Box>
      <SwipeableViews
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
                <others.component
                  marketCodeSelectorRef={marketCodeSelectorRef}
                  marketCodeCombination={selectedMarketCodeCombination}
                  queryKey={queryKey}
                  tradeConfigAllocations={tradeConfigAllocations}
                  tradeConfigUuids={tradeConfigUuids}
                  onChangeTabHandler={(newTab) => setCurrentTab(newTab)}
                />
              </Box>
            )}
          </TabPanel>
        ))}
      </SwipeableViews>
    </Box>
  );
}
