import React, { useEffect, useMemo, useRef, useState } from 'react';

import {
  Link,
  Navigate,
  Outlet,
  useLocation,
  useNavigate,
} from 'react-router-dom';

import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import { useSelector } from 'react-redux';

import { useTranslation } from 'react-i18next';
import i18n from 'configs/i18n';

import { useVisibilityChange } from '@uidotdev/usehooks';

import a11yProps from 'utils/a11yProps';


const TAB = {
  dashboard: '/affiliate/dashboard',
  commissionHistory: '/affiliate/commission-history',
};

const TABS = [
  {
    id: TAB.triggers,
    name: '/affiliate/dashboard',
    getLabel: () => i18n.t('Affiliate Dashboard'),
  },
  {
    id: TAB.position,
    name: '/affiliate/commission-history',
    getLabel: () => i18n.t('Commission History'),
  },
];

export default function Bot() {
  const { t } = useTranslation();

  const isFocused = useVisibilityChange();

  const theme = useTheme();
  const location = useLocation();
  const navigate = useNavigate();

  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const { loggedin, user } = useSelector((state) => state.auth);

  useEffect(() => () => window.history.replaceState(null, ''), []);


  return (
    <Box sx={{ flex: 1, overflowX: 'hidden' }}>
      <Box sx={isMobile ? { maxWidth: window.innerWidth * 0.95 } : {}}>
        <Grid container sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Grid item md xs={12}>
            {location.pathname === '/affiliate' ? (
              <Box />
            ) : (
              <Tabs
                allowScrollButtonsMobile
                scrollButtons
                aria-label="affiliate-tabs"
                variant="scrollable"
                value={location.pathname}
                // value={currentTab}
                // onChange={(e, newValue) => setCurrentTab(newValue)}
                sx={{ borderBottom: 0, mb: 0 }}
              >
                {TABS.map(({ id, name, disabled, getLabel }) => (
                  <Tab
                    component={Link}
                    key={name}
                    label={getLabel()}
                    value={name}
                    to={name}
                    {...a11yProps({ id, name })}
                  />
                ))}
              </Tabs>
            )}
          </Grid>
        </Grid>
      </Box>
      <Outlet />
    </Box>
  );
}