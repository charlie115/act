import React from 'react';

import { useOutletContext } from 'react-router-dom';

import AlarmSupportBotSettings from 'components/AlarmSupportBotSettings';
import TradeSupportBotSettings from 'components/TradeSupportBotSettings';
import VolatilityNotificationSettings from 'components/VolatilityNotificationSettings';

export default function Settings() {
  const { marketCodeSelectorRef, marketCodeCombination } = useOutletContext();

  // Show volatility notification settings when ALL is selected
  if (!marketCodeCombination || marketCodeCombination?.value === 'ALL') {
    return <VolatilityNotificationSettings marketCodeSelectorRef={marketCodeSelectorRef} />;
  }

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
