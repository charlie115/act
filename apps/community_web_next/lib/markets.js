const EXCHANGE_LABELS = {
  BINANCE: "Binance",
  BITHUMB: "Bithumb",
  BYBIT: "Bybit",
  COINONE: "Coinone",
  GATE: "Gate",
  HYPERLIQUID: "Hyperliquid",
  OKX: "OKX",
  UPBIT: "Upbit",
};

function formatMarketType(marketType, quoteAsset) {
  if (marketType === "SPOT") {
    return quoteAsset ? `Spot (${quoteAsset})` : "Spot";
  }

  if (marketType === "USD_M") {
    return quoteAsset ? `USD-M (${quoteAsset})` : "USD-M";
  }

  if (marketType === "COIN_M") {
    return quoteAsset ? `COIN-M (${quoteAsset})` : "COIN-M";
  }

  return quoteAsset ? `${marketType} (${quoteAsset})` : marketType;
}

export function getMarketOption(marketCode) {
  if (!marketCode) {
    return null;
  }

  const [marketName, quoteAsset] = marketCode.split("/");
  const parts = marketName.split("_");
  const exchange = parts[0];
  const marketType = parts.slice(1).join("_");
  const exchangeLabel = EXCHANGE_LABELS[exchange] || exchange;
  const label = `${exchangeLabel} ${formatMarketType(marketType, quoteAsset)}`.trim();

  return {
    exchange,
    getLabel: () => label,
    isSpot: marketType === "SPOT",
    label,
    value: marketCode,
  };
}
