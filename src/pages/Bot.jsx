import React, { useEffect, useMemo, useRef, useState } from 'react';

import { Navigate, useLocation } from 'react-router-dom';

import SwipeableViews from 'react-swipeable-views';

import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';

import CheckBoxIcon from '@mui/icons-material/CheckBox';

import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import { useSelector } from 'react-redux';

import { useTranslation } from 'react-i18next';
import i18n from 'configs/i18n';

import a11yProps from 'utils/a11yProps';

import TabPanel from 'components/TabPanel';

import BotSettings from 'components/BotSettings';
import MarketCodeCombinationSelector from 'components/MarketCodeCombinationSelector';
import TriggersTable from 'components/tables/trigger/TriggersTable';

import { MARKET_CODE_LIST } from 'constants/lists';

const TABS = [
  {
    id: 0,
    name: 'triggers',
    getLabel: () => i18n.t('Triggers'),
    component: TriggersTable,
  },
  {
    id: 1,
    name: 'botSettings',
    getLabel: () => i18n.t('BOT Settings'),
    component: BotSettings,
  },
  {
    id: 2,
    name: 'apiKeySettings',
    getLabel: () => i18n.t('API Key Settings'),
    component: Box,
  },
  {
    id: 3,
    name: 'userGuide',
    getLabel: () => i18n.t('User Guide'),
    component: Box,
  },
  {
    id: 4,
    name: 'supportCenter',
    getLabel: () => i18n.t('Support Center'),
    component: Box,
  },
];

export default function Bot() {
  const marketCodeSelectorRef = useRef();

  const {
    i18n: { language },
    t,
  } = useTranslation();

  const theme = useTheme();
  const location = useLocation();

  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const { loggedin, user } = useSelector((state) => state.auth);

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

  const [currentTab, setCurrentTab] = useState(0);
  const [marketCodeCombinationList, setMarketCodeCombinationList] = useState(
    []
  );
  const [selectedMarketCodeCombination, setSelectedMarketCodeCombination] =
    useState();

  useEffect(() => {
    const marketCodes = [
      {
        label: t('All'),
        value: 'ALL',
        icon: <CheckBoxIcon />,
      },
    ].concat(
      tradeConfigAllocations?.map((item) => ({
        value: item.value,
        target: {
          label: item.target.getLabel(),
          icon: (
            <Box
              component="img"
              src={item.target.icon}
              alt={item.target.getLabel()}
              sx={{
                height: { xs: 16, md: 18 },
                width: { xs: 16, md: 18 },
              }}
            />
          ),
        },
        origin: {
          label: item.origin.getLabel(),
          icon: (
            <Box
              component="img"
              src={item.origin.icon}
              alt={item.origin.getLabel()}
              sx={{
                height: { xs: 16, md: 18 },
                width: { xs: 16, md: 18 },
              }}
            />
          ),
        },
        tradeConfigUuid: item.uuid,
      }))
    );
    setMarketCodeCombinationList(marketCodes);
    if (!selectedMarketCodeCombination)
      setSelectedMarketCodeCombination(marketCodes[0]);
  }, [selectedMarketCodeCombination, tradeConfigAllocations, language]);

  if (!loggedin)
    return <Navigate replace to="/login" state={{ from: location }} />;

  return (
    <Box sx={{ flex: 1 }}>
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
                  disabled={name !== 'triggers' && name !== 'botSettings'}
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
              onSelectItem={setSelectedMarketCodeCombination}
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
                  selectedMarketCodeCombination={selectedMarketCodeCombination}
                  tradeConfigAllocations={tradeConfigAllocations}
                  tradeConfigUuids={tradeConfigUuids}
                />
              </Box>
            )}
          </TabPanel>
        ))}
      </SwipeableViews>
    </Box>
  );
}
