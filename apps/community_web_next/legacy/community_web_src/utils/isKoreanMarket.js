const KOREAN_MARKET_PREFIXES = ['upbit', 'bithumb'];

export default (marketCode) =>
  KOREAN_MARKET_PREFIXES.findIndex((el) =>
    marketCode?.toLowerCase()?.includes(el)
  ) >= 0;
