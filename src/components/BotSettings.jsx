import React from 'react';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';

import { useTranslation } from 'react-i18next';

import AlarmSupportBotSettings from 'components/AlarmSupportBotSettings';
import TradeSupportBotSettings from 'components/TradeSupportBotSettings';

export default function BotSettings({
  marketCodeSelectorRef,
  marketCodeCombination,
}) {
  if (marketCodeCombination?.tradeSupport)
    return (
      <TradeSupportBotSettings
        marketCodeSelectorRef={marketCodeSelectorRef}
        marketCodeCombination={marketCodeCombination}
      />
    );
  return (
    <AlarmSupportBotSettings
      marketCodeSelectorRef={marketCodeSelectorRef}
      marketCodeCombination={marketCodeCombination}
    />
  );
}
