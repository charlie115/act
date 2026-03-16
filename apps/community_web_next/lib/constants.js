export const API_BASE = process.env.NEXT_PUBLIC_DRF_URL || "";

export const USER_ROLE = {
  ADMIN: "admin",
  STAFF: "staff",
  USER: "user",
};

export const MARKET_TYPES = {
  SPOT: "SPOT",
  USD_M: "USD_M",
  COIN_M: "COIN_M",
};

export const EXCHANGE_LABELS = {
  UPBIT: "업비트",
  BITHUMB: "빗썸",
  COINONE: "코인원",
  BINANCE: "바이낸스",
  BYBIT: "바이비트",
  OKX: "OKX",
  GATE: "게이트",
  HYPERLIQUID: "하이퍼리퀴드",
};

export function getBrowserTimezone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch {
    return "Asia/Seoul";
  }
}
