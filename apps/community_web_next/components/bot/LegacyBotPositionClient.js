"use client";

import PositionTable from "components/tables/position/PositionTable";

export default function LegacyBotPositionClient({ marketCodeCombination }) {
  return (
    <div className="legacy-surface legacy-surface--bot">
      <PositionTable marketCodeCombination={marketCodeCombination} />
    </div>
  );
}
