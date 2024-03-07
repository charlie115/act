import React, { useEffect, useState } from 'react';

import Badge from '@mui/material/Badge';

import ForumIcon from '@mui/icons-material/Forum';
import TelegramIcon from '@mui/icons-material/Telegram';

import { useTranslation } from 'react-i18next';
import i18n from 'configs/i18n';

import DropdownMenu from 'components/DropdownMenu';

const CHANNELS = [
  {
    id: 0,
    value: 'telegram',
    icon: TelegramIcon,
    getLabel: () => i18n.t('Telegram'),
  },
  {
    id: 1,
    value: 'community',
    icon: ForumIcon,
    getLabel: () => i18n.t('Community'),
  },
];

export default function ChatChannelSelector({ badges, onChange }) {
  const {
    i18n: { language },
    t,
  } = useTranslation();

  const [options, setOptions] = useState([]);
  const [value, setValue] = useState(null);

  const [showBadge, setShowBadge] = useState(false);

  useEffect(() => {
    onChange(value);
  }, [value]);

  useEffect(() => {
    setOptions((state) =>
      state.map((item) => ({ ...item, showBadge: badges[item.value] }))
    );
    setShowBadge(
      Object.values(badges || {}).filter((item) => !!item)?.length > 0
    );
  }, [badges]);

  useEffect(() => {
    const channels = CHANNELS.map((channel) => ({
      ...channel,
      label: channel.getLabel(),
      icon: <channel.icon />,
      showBadge: badges[channel.value],
    }));
    setOptions(channels);
    setValue(channels[0]);
  }, [language]);

  return (
    <DropdownMenu
      value={value}
      options={options}
      onSelectItem={setValue}
      showBadge={showBadge}
      buttonProps={{ size: 'small', variant: 'text' }}
      buttonStyle={{ minWidth: 'unset', width: 140 }}
      containerStyle={{ ml: 2, mr: 'auto' }}
    />
  );
}
