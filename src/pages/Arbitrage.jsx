import React, { useMemo, useState } from 'react';

import { useLocation } from 'react-router-dom';

import SwipeableViews from 'react-swipeable-views';

import Badge from '@mui/material/Badge';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';

import { styled, useTheme } from '@mui/material/styles';

import { useTranslation } from 'react-i18next';

import a11yProps from 'utils/a11yProps';

import ArbitrageTable from 'components/ArbitrageTable';
import FundingRateDiffTable from 'components/funding_rate/FundingRateDiffTable';
import StyledTab from 'components/StyledTab';
import StyledTabs from 'components/StyledTabs';
import TabPanel from 'components/TabPanel';

const ARBITRAGE_TAB = { fundingRateDifference: 0 };

export default function Arbitrage() {
  const { t } = useTranslation();
  const location = useLocation();
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
          <Box sx={{ overflowX: 'hidden', mb: 2, p: 1 }}>
            <FundingRateDiffTable />
          </Box>
        </TabPanel>
      </SwipeableViews>
    </Box>
  );
}
