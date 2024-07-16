import React from 'react';

import { Link, Outlet, useLocation } from 'react-router-dom';

import Box from '@mui/material/Box';
import LinearProgress from '@mui/material/LinearProgress';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';

import i18n from 'configs/i18n';
import a11yProps from 'utils/a11yProps';

import AvgFundingRateTable from 'components/tables/funding_rate/AvgFundingRateTable';
import FundingRateDiffTable from 'components/tables/funding_rate/FundingRateDiffTable';

const TABS = [
  {
    id: 0,
    value: '/arbitrage/funding-rate/diff',
    component: FundingRateDiffTable,
    getLabel: () => i18n.t('Funding Rate Difference'),
  },
  {
    id: 1,
    value: '/arbitrage/funding-rate/avg',
    component: AvgFundingRateTable,
    getLabel: () => i18n.t('Average Funding Rate'),
  },
];

export default function Arbitrage() {
  const location = useLocation();

  return (
    <Box sx={{ flex: 1 }}>
      {location.pathname === '/arbitrage' ? (
        <LinearProgress />
      ) : (
        <Tabs aria-label="arbitrage-tabs" value={location.pathname}>
          {TABS.map(({ id, value, getLabel }) => (
            <Tab
              component={Link}
              key={value}
              label={getLabel()}
              to={value}
              value={value}
              {...a11yProps({ id, name: value })}
            />
          ))}
        </Tabs>
      )}
      <Outlet />
    </Box>
  );
}
