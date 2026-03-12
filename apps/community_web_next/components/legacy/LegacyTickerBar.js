"use client";

import TVTickerWidget from "components/trading_view/TVTickerWidget";

export default function LegacyTickerBar() {
  return (
    <div className="legacy-surface legacy-surface--ticker">
      <TVTickerWidget isVisible />
    </div>
  );
}
