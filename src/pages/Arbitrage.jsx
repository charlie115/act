import React, { useState } from 'react';

import SwipeableViews from 'react-swipeable-views';

import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';

import { useTheme } from '@mui/material/styles';

import { useTranslation } from 'react-i18next';

import a11yProps from 'utils/a11yProps';

import AvgFundingRateTable from 'components/tables/funding_rate/AvgFundingRateTable';
import FundingRateDiffTable from 'components/tables/funding_rate/FundingRateDiffTable';
import StyledTab from 'components/StyledTab';
import StyledTabs from 'components/StyledTabs';
import TabPanel from 'components/TabPanel';

const ARBITRAGE_TAB = { fundingRateDifference: 0, averageFundingRate: 1 };

export default function Arbitrage() {
  const { t } = useTranslation();
  const theme = useTheme();

  const [currentTab, setCurrentTab] = useState(
    ARBITRAGE_TAB.fundingRateDifference
  );

  return (
    <Box sx={{ flex: 1 }}>
      <Stack
        alignItems="center"
        justifyContent="space-between"
        direction="row"
        spacing={{ xs: 1, sm: 2 }}
        sx={{
          borderBottom: 1,
          borderColor: 'divider',
          mb: 1,
        }}
      >
        <StyledTabs
          aria-label="arbitrage-tabs"
          value={currentTab}
          onChange={(e, newValue) => setCurrentTab(newValue)}
        >
          <StyledTab
            label={t('Funding Rate Difference')}
            value={ARBITRAGE_TAB.fundingRateDifference}
            {...a11yProps({
              name: 'arbitrage',
              id: ARBITRAGE_TAB.fundingRateDifference,
            })}
          />
          <StyledTab
            label={t('Average Funding Rate')}
            value={ARBITRAGE_TAB.averageFundingRate}
            {...a11yProps({
              name: 'arbitrage',
              id: ARBITRAGE_TAB.averageFundingRate,
            })}
          />
        </StyledTabs>
      </Stack>
      <SwipeableViews
        axis={theme.direction === 'rtl' ? 'x-reverse' : 'x'}
        index={currentTab}
        onChangeIndex={(newIndex) => setCurrentTab(newIndex)}
      >
        <TabPanel
          index={ARBITRAGE_TAB.fundingRateDifference}
          dir={theme.direction}
          value={currentTab}
        >
          {currentTab === ARBITRAGE_TAB.fundingRateDifference && (
            <Box sx={{ overflowX: 'hidden', mb: 2, p: 1 }}>
              <FundingRateDiffTable />
            </Box>
          )}
        </TabPanel>
        <TabPanel
          index={ARBITRAGE_TAB.averageFundingRate}
          dir={theme.direction}
          value={currentTab}
        >
          {currentTab === ARBITRAGE_TAB.averageFundingRate && (
            <Box sx={{ overflowX: 'hidden', mb: 2, p: 1 }}>
              <AvgFundingRateTable />
            </Box>
          )}
        </TabPanel>
      </SwipeableViews>
    </Box>
  );
}
