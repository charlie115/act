import React, { useEffect, useMemo, useRef, useState } from 'react';

import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Divider from '@mui/material/Divider';
import Stack from '@mui/material/Stack';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import Typography from '@mui/material/Typography';

import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import CheckBoxIcon from '@mui/icons-material/CheckBox';
import NotificationsIcon from '@mui/icons-material/Notifications';

import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import { useSelector } from 'react-redux';

import { useLoginTelegramMutation } from 'redux/api/drf/auth';
import { useGetNodesQuery } from 'redux/api/drf/tradecore';

import { useTranslation } from 'react-i18next';

import useScript from 'hooks/useScript';
import a11yProps from 'utils/a11yProps';

import CreateAlarmForm from 'components/CreateAlarmForm';
import TabPanel from 'components/TabPanel';

import AlarmsTable from 'components/tables/trigger/AlarmsTable';

const CONFIGURATION_TAB = { alarm: 0, autoTrade: 1, all: 2 };

function AssetTradeConfigTriggers({
  baseAsset,
  marketCodes,
  isTetherPriceView,
  onAlarmConfigChange,
}) {
  const alarmsTableRef = useRef();
  const createAlarmFormRef = useRef();

  const { t } = useTranslation();

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [loginTelegram] = useLoginTelegramMutation();
  const { telegramBot, user } = useSelector((state) => state.auth);

  const { data: nodes } = useGetNodesQuery(
    {
      marketCodeServices: `${marketCodes?.targetMarketCode}:${marketCodes?.originMarketCode}`,
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

  const dataOnAuth = (telegramUser) => {
    loginTelegram({ user: user?.uuid, ...telegramUser });
  };

  useEffect(() => {
    window.TelegramWidget = { dataOnAuth };
  }, []);

  useScript(
    telegramBot && user && !user?.telegram_chat_id && nodes?.results.length > 0
      ? 'https://telegram.org/js/telegram-widget.js?22'
      : null,
    {
      nodeId: 'telegram-trade-config-button',
      attributes: {
        'data-onauth': 'TelegramWidget.dataOnAuth(user)',
        'data-request-access': 'write',
        'data-telegram-login': telegramBot,
        'data-size': 'medium',
      },
    },
    []
  );

  if (nodes?.results.length > 0)
    return (
      <Card onClick={(e) => e.stopPropagation()} sx={{ borderRadius: 0 }}>
        <Box sx={{ bgcolor: 'background.paper', p: 2 }}>
          <Divider />
          <Box sx={isMobile ? undefined : { display: 'flex', flexGrow: 1 }}>
            <Tabs
              aria-label="configuration-tabs"
              value={currentTab}
              orientation={isMobile ? 'horizontal' : 'vertical'}
              variant="standard"
              onChange={(e, newValue) => setCurrentTab(newValue)}
              sx={
                isMobile
                  ? undefined
                  : { borderRight: 1, borderColor: 'divider', width: 150 }
              }
            >
              <Tab
                icon={<NotificationsIcon />}
                iconPosition="start"
                label={t('Alarm')}
                value={CONFIGURATION_TAB.alarm}
                sx={{ minHeight: 45, justifyContent: 'flex-start' }}
                {...a11yProps({
                  name: 'configuration',
                  id: CONFIGURATION_TAB.alarm,
                })}
              />
              <Tab
                disabled
                icon={<AccountBalanceWalletIcon />}
                iconPosition="start"
                label={t('Auto Trade')}
                value={CONFIGURATION_TAB.autoTrade}
                sx={{ minHeight: 45, justifyContent: 'flex-start' }}
                {...a11yProps({
                  name: 'configuration',
                  id: CONFIGURATION_TAB.autoTrade,
                })}
              />
              <Tab
                disabled
                icon={<CheckBoxIcon />}
                iconPosition="start"
                label={t('All')}
                value={CONFIGURATION_TAB.all}
                sx={{ minHeight: 45, justifyContent: 'flex-start' }}
                {...a11yProps({
                  name: 'all',
                  id: CONFIGURATION_TAB.all,
                })}
              />
            </Tabs>
            {user?.telegram_chat_id ? (
              <>
                <TabPanel
                  id="asset-trading-config"
                  index={CONFIGURATION_TAB.alarm}
                  dir={theme.direction}
                  value={currentTab}
                  style={{ flex: 1 }}
                >
                  {currentTab === CONFIGURATION_TAB.alarm && (
                    <>
                      <CreateAlarmForm
                        ref={createAlarmFormRef}
                        baseAsset={baseAsset}
                        marketCodes={marketCodes}
                        isTetherPriceView={isTetherPriceView}
                        tradeConfigAllocation={tradeConfigAllocation}
                        onAlarmConfigChange={onAlarmConfigChange}
                      />
                      <AlarmsTable
                        createAlarmFormRef={createAlarmFormRef}
                        baseAsset={baseAsset}
                        tradeConfigAllocation={tradeConfigAllocation}
                        onAlarmConfigChange={onAlarmConfigChange}
                      />
                    </>
                  )}
                </TabPanel>
                <TabPanel
                  id="asset-trading-config"
                  index={CONFIGURATION_TAB.autoTrade}
                  dir={theme.direction}
                  value={currentTab}
                  style={{ flex: 1 }}
                >
                  AutoTrade
                  {/* {currentTab === CONFIGURATION_TAB.autoTrade && (
                <Box sx={{ height: '100%', overflowX: 'hidden', mb: 2, p: 1 }}>
                  Auto Trade
                </Box>
              )} */}
                </TabPanel>
                <TabPanel
                  id="all-config"
                  index={CONFIGURATION_TAB.all}
                  dir={theme.direction}
                  value={currentTab}
                  style={{ flex: 1 }}
                >
                  All
                  {/* {currentTab === CONFIGURATION_TAB.autoTrade && (
                <Box sx={{ height: '100%', overflowX: 'hidden', mb: 2, p: 1 }}>
                  Auto Trade
                </Box>
              )} */}
                </TabPanel>
              </>
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
                <Box id="telegram-trade-config-button" />
              </Stack>
            )}
          </Box>
        </Box>
      </Card>
    );

  return null;
}

export default React.memo(AssetTradeConfigTriggers);
