"use client";

import CapitalTable from "components/tables/capital/CapitalTable";

export default function LegacyBotCapitalClient({ marketCodeCombination }) {
  return (
    <div className="legacy-surface legacy-surface--bot">
      <CapitalTable marketCodeCombination={marketCodeCombination} />
    </div>
  );
}
