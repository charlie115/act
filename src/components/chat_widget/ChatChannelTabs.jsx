import React, { useState } from 'react';

import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';

import { useTranslation } from 'react-i18next';
import i18n from 'configs/i18n';

import a11yProps from 'utils/a11yProps';

const TABS = [
  {
    id: 0,
    name: 'telegram',
    getLabel: () => i18n.t('Telegram'),
  },
  {
    id: 1,
    name: 'community',
    getLabel: () => i18n.t('Community'),
  },
];

export default function ChatChannelTabs() {
  const [currentTab, setCurrentTab] = useState(0);

  return (
    <Tabs
      allowScrollButtonsMobile
      scrollButtons
      aria-label="chat-channel-tabs"
      variant="scrollable"
      value={currentTab}
      onChange={(e, newValue) => setCurrentTab(newValue)}
      sx={{ borderBottom: 0, mb: 1 }}
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
  );
}
