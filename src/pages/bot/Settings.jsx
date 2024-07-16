import React from 'react';

import { useOutletContext } from 'react-router-dom';

import AlarmSupportBotSettings from 'components/AlarmSupportBotSettings';
import TradeSupportBotSettings from 'components/TradeSupportBotSettings';

export default function Settings() {
  const { marketCodeSelectorRef, marketCodeCombination } = useOutletContext();

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
