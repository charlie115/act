"use client";

import { useMemo, useState } from "react";

import ScannerTable from "components/tables/scanner/ScannerTable";

export default function LegacyBotScannerClient({
  marketCodeCombination,
  tradeConfigAllocations,
  tradeConfigUuids,
}) {
  const [queryKey] = useState(() => Date.now());

  const normalizedMarketCodeCombination = useMemo(() => {
    if (!marketCodeCombination) {
      return null;
    }

    return {
      ...marketCodeCombination,
      tradeConfigUuid:
        marketCodeCombination.tradeConfigUuid || marketCodeCombination.trade_config_uuid,
    };
  }, [marketCodeCombination]);

  return (
    <div className="legacy-surface legacy-surface--bot">
      <ScannerTable
        _queryKey={queryKey}
        marketCodeCombination={normalizedMarketCodeCombination}
        tradeConfigAllocations={tradeConfigAllocations}
        tradeConfigUuids={tradeConfigUuids}
      />
    </div>
  );
}
