import React, { useMemo, useRef, useState } from 'react';

import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Divider from '@mui/material/Divider';
import Stack from '@mui/material/Stack';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import Typography from '@mui/material/Typography';

import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import { useSelector } from 'react-redux';

import { useGetNodesQuery } from 'redux/api/drf/tradecore';

import { useTranslation } from 'react-i18next';

import sortBy from 'lodash/sortBy';

import a11yProps from 'utils/a11yProps';

import CreateTriggerForm from 'components/CreateTriggerForm';

import TradesTable from 'components/tables/trigger/TradesTable';

import { TRIGGER_LIST } from 'constants/lists';

import TelegramLoginButton from './TelegramLoginButton';

const CONFIGURATION_TAB = { alarm: 0, autoTrade: 1, all: 2 };

const TABS = sortBy(
  TRIGGER_LIST.filter((i) => i.value !== 'ALL'),
  'tabId'
).map((trigger) => ({
  ...trigger,
}));

function AssetTradeConfig({
  baseAsset,
  interval,
  marketCodes,
  isTetherPriceView,
  onCreateSuccess,
  onTriggerConfigChange,
  premiumDataViewerRef,
  showTable,
}) {
  const createTriggerFormRef = useRef();

  const { t } = useTranslation();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const { user } = useSelector((state) => state.auth);

  const { data: nodes } = useGetNodesQuery(
    {
      market_code_combinations: `${marketCodes?.targetMarketCode}:${marketCodes?.originMarketCode}`,
    },
    { skip: !marketCodes }
  );

  const [currentTab, setCurrentTab] = useState(CONFIGURATION_TAB.alarm);

  const tradeConfigAllocation = useMemo(
    () =>
      user?.trade_config_allocations?.find(
        (o) =>
          o.target_market_code === marketCodes?.targetMarketCode &&
          o.origin_market_code === marketCodes?.originMarketCode
      ),
    [marketCodes, user?.trade_config_allocations]
  );

  const tradeSupport = useMemo(() => {
    if (!nodes?.results?.[0]?.market_code_combinations) return false;
    const combination = nodes.results[0].market_code_combinations.find(
      (combo) => combo.market_code_combination === `${marketCodes?.targetMarketCode}:${marketCodes?.originMarketCode}`
    );
    return combination?.trade_support ?? false;
  }, [nodes, marketCodes]);

  if (nodes?.results.length > 0)
    return (
      <Card onClick={(e) => e.stopPropagation()} sx={{ borderRadius: 0 }}>
        <Box sx={{ bgcolor: 'background.paper', p: 2 }}>
          <Divider />
          <Box sx={isMobile ? undefined : { display: 'flex', flexGrow: 1 }}>
            <Tabs
              allowScrollButtonsMobile
              scrollButtons
              aria-label="configuration-tabs"
              value={currentTab}
              orientation={isMobile ? 'horizontal' : 'vertical'}
              variant={isMobile ? 'scrollable' : 'standard'}
              onChange={async (e, newValue) => {
                if (newValue === CONFIGURATION_TAB.autoTrade && !tradeSupport) {
                  return;
                }
                setCurrentTab(newValue);
              }}
              sx={
                isMobile
                  ? undefined
                  : { borderRight: 1, borderColor: 'divider', width: 150 }
              }
            >
              {TABS.map((tab) => (
                <Tab
                  key={tab.value}
                  icon={<tab.icon />}
                  iconPosition="start"
                  label={tab.getLabel()}
                  value={tab.tabId}
                  disabled={tab.tabId === CONFIGURATION_TAB.autoTrade ? !tradeSupport : tab.disabled}
                  sx={{ minHeight: 45, justifyContent: 'flex-start' }}
                  {...a11yProps(tab)}
                />
              ))}
            </Tabs>
            {user?.telegram_chat_id ? (
              <Box sx={{ flex: 1 }}>
                <CreateTriggerForm
                  ref={createTriggerFormRef}
                  premiumDataViewerRef={premiumDataViewerRef}
                  baseAsset={baseAsset}
                  interval={interval}
                  marketCodes={marketCodes}
                  tradeType={
                    currentTab === CONFIGURATION_TAB.alarm
                      ? 'alarm'
                      : 'autoTrade'
                  }
                  isTetherPriceView={isTetherPriceView}
                  tradeConfigAllocation={tradeConfigAllocation}
                  onCreateSuccess={onCreateSuccess}
                  onTriggerConfigChange={onTriggerConfigChange}
                />
                {showTable && (
                  <TradesTable
                    tradeType={
                      currentTab === CONFIGURATION_TAB.alarm
                        ? 'alarm'
                        : 'autoTrade'
                    }
                    createTriggerFormRef={createTriggerFormRef}
                    baseAsset={baseAsset}
                    tradeConfigAllocation={tradeConfigAllocation}
                    onTriggerConfigChange={onTriggerConfigChange}
                  />
                )}
              </Box>
            ) : (
              <Stack
                spacing={2}
                alignItems="center"
                justifyContent="center"
                sx={{ width: '100%' }}
              >
                <Typography sx={{ color: 'error.main' }}>
                  {t('Connect to Telegram to enable this setting')}
                </Typography>
                <TelegramLoginButton buttonId="telegram-trade-config-button" />
              </Stack>
            )}
          </Box>
        </Box>
      </Card>
    );

  return null;
}

export default React.memo(AssetTradeConfig);