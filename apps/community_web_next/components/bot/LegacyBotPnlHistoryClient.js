"use client";

import PnLHistory from "pages/bot/PnLHistory";
import LegacyOutletContextRouter from "../legacy/LegacyOutletContextRouter";

export default function LegacyBotPnlHistoryClient({ marketCodeCombination }) {
  return (
    <div className="legacy-surface legacy-surface--bot">
      <LegacyOutletContextRouter context={{ marketCodeCombination }}>
        <PnLHistory />
      </LegacyOutletContextRouter>
    </div>
  );
}
