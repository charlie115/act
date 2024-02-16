import React, { useState } from 'react';

import { Navigate, useLocation } from 'react-router-dom';

import SwipeableViews from 'react-swipeable-views';

import Box from '@mui/material/Box';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';

import { useTheme } from '@mui/material/styles';

import { useSelector } from 'react-redux';

import i18n from 'configs/i18n';

import a11yProps from 'utils/a11yProps';

import TabPanel from 'components/TabPanel';

import TriggersTable from 'components/tables/trigger/TriggersTable';

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
    component: Box,
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
  const theme = useTheme();
  const location = useLocation();

  const loggedin = useSelector((state) => state.auth.loggedin);

  const [currentTab, setCurrentTab] = useState(0);

  if (!loggedin)
    return <Navigate replace to="/login" state={{ from: location }} />;

  return (
    <Box sx={{ flex: 1 }}>
      <Box sx={{ maxWidth: window.innerWidth * 0.95 }}>
        <Tabs
          allowScrollButtonsMobile
          scrollButtons
          aria-label="arbitrage-tabs"
          variant="scrollable"
          value={currentTab}
          onChange={(e, newValue) => setCurrentTab(newValue)}
        >
          {TABS.map(({ id, name, getLabel }) => (
            <Tab
              key={name}
              label={getLabel()}
              value={id}
              {...a11yProps({ id, name })}
            />
          ))}
        </Tabs>
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
                <others.component />
              </Box>
            )}
          </TabPanel>
        ))}
      </SwipeableViews>
    </Box>
  );
}
