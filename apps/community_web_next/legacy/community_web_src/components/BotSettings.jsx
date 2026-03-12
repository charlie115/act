import React from 'react';

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
