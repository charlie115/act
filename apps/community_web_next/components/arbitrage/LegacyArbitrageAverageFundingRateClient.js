"use client";

import AvgFundingRateTable from "components/tables/funding_rate/AvgFundingRateTable";

export default function LegacyArbitrageAverageFundingRateClient() {
  return (
    <div className="legacy-surface legacy-surface--arbitrage">
      <AvgFundingRateTable />
    </div>
  );
}
