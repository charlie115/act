"use client";

import AlarmSupportBotSettings from "components/AlarmSupportBotSettings";
import TradeSupportBotSettings from "components/TradeSupportBotSettings";
import VolatilityNotificationSettings from "components/VolatilityNotificationSettings";

export default function LegacyBotSettingsClient({ marketCodeCombination, marketCodeSelectorRef }) {
  if (!marketCodeCombination || marketCodeCombination.value === "ALL") {
    return (
      <div className="legacy-surface legacy-surface--bot">
        <VolatilityNotificationSettings marketCodeSelectorRef={marketCodeSelectorRef} />
      </div>
    );
  }

  if (marketCodeCombination.tradeSupport) {
    return (
      <div className="legacy-surface legacy-surface--bot">
        <TradeSupportBotSettings marketCodeCombination={marketCodeCombination} />
      </div>
    );
  }

  return (
    <div className="legacy-surface legacy-surface--bot">
      <AlarmSupportBotSettings
        marketCodeCombination={marketCodeCombination}
        marketCodeSelectorRef={marketCodeSelectorRef}
      />
    </div>
  );
}
