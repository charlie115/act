import React, { useEffect, useState } from 'react';

import { Link, Outlet, useLocation } from 'react-router-dom';

import Box from '@mui/material/Box';
import LinearProgress from '@mui/material/LinearProgress';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';

import { useTranslation } from 'react-i18next';

import i18n from 'configs/i18n';
import a11yProps from 'utils/a11yProps';

const TABS = [
  {
    id: 0,
    value: '/arbitrage/funding-rate/diff',
    getLabel: () => i18n.t('Funding Rate Difference'),
  },
  {
    id: 2,
    value: '/arbitrage/funding-rate/avg',
    getLabel: () => i18n.t('Average Funding Rate'),
  },
];

export default function Arbitrage() {
  const location = useLocation();

  const {
    i18n: { language },
  } = useTranslation();

  const [tabs, setTabs] = useState([]);

  useEffect(() => {
    setTabs(TABS.map((tab) => ({ ...tab, label: tab.getLabel() })));
  }, [language]);

  return (
    <Box sx={{ flex: 1 }}>
      {location.pathname === '/arbitrage' ? (
        <LinearProgress />
      ) : (
        <Tabs aria-label="arbitrage-tabs" value={location.pathname}>
          {tabs.map(({ id, value, label }) => (
            <Tab
              component={Link}
              key={value}
              label={label}
              to={value}
              value={value}
              {...a11yProps({ id, name: value })}
            />
          ))}
        </Tabs>
      )}
      <Box sx={{ p: 1 }}>
        <Outlet />
      </Box>
    </Box>
  );
}
