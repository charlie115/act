"use client";

import { useMemo, useState } from "react";

import TriggersTable from "components/tables/trigger/TriggersTable";

export default function LegacyBotTriggersClient({
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
      <TriggersTable
        marketCodeCombination={normalizedMarketCodeCombination}
        queryKey={queryKey}
        tradeConfigAllocations={tradeConfigAllocations}
        tradeConfigUuids={tradeConfigUuids}
      />
    </div>
  );
}
