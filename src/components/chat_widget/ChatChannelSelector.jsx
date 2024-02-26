import React, { useEffect, useState } from 'react';

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

export default function ChatChannelSelector({ onChange }) {
  const {
    i18n: { language },
    t,
  } = useTranslation();

  const [options, setOptions] = useState([]);
  const [value, setValue] = useState(null);

  useEffect(() => {
    onChange(value);
  }, [value]);

  useEffect(() => {
    const channels = CHANNELS.map((channel) => ({
      ...channel,
      label: channel.getLabel(),
      icon: <channel.icon />,
    }));
    setOptions(channels);
    setValue(channels[0]);
  }, [language]);

  return (
    <DropdownMenu
      value={value}
      options={options}
      onSelectItem={setValue}
      buttonProps={{ size: 'small', variant: 'text' }}
      buttonStyle={{ minWidth: 'unset', width: 140 }}
      containerStyle={{ ml: 2, mr: 'auto' }}
    />
  );
}
