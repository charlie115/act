import React, { useState } from 'react';

import SwipeableViews from 'react-swipeable-views';

import Box from '@mui/material/Box';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';

import { useTheme } from '@mui/material/styles';

import i18n from 'configs/i18n';
import a11yProps from 'utils/a11yProps';

import AvgFundingRateTable from 'components/tables/funding_rate/AvgFundingRateTable';
import FundingRateDiffTable from 'components/tables/funding_rate/FundingRateDiffTable';
import TabPanel from 'components/TabPanel';

const TABS = [
  {
    id: 0,
    name: 'fundingRateDifference',
    component: FundingRateDiffTable,
    getLabel: () => i18n.t('Funding Rate Difference'),
  },
  {
    id: 1,
    name: 'averageFundingRate',
    component: AvgFundingRateTable,
    getLabel: () => i18n.t('Average Funding Rate'),
  },
];

export default function Arbitrage() {
  const theme = useTheme();

  const [currentTab, setCurrentTab] = useState(0);

  return (
    <Box sx={{ flex: 1 }}>
      <Tabs
        aria-label="arbitrage-tabs"
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
