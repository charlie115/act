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

export const REGEX = {
  chatMention: /\B@([\w_]+)/,
  // eslint-disable-next-line no-control-regex
  ctrlCharactersRegex: /[\u0000-\u001F\u007F-\u009F\u2000-\u200D\uFEFF]/gim,
  spotMarketSuffix: /(_SPOT\/)([A-Z]+)/,
  koreanCharacters:
    /[\uac00-\ud7af]|[\u1100-\u11ff]|[\u3130-\u318f]|[\ua960-\ua97f]|[\ud7b0-\ud7ff]$/i,
  usernameFirstCharacter:
    /^[A-Za-z]|[\uac00-\ud7af]|[\u1100-\u11ff]|[\u3130-\u318f]|[\ua960-\ua97f]|[\ud7b0-\ud7ff]/i,
  usernameFull:
    /^([A-Za-z0-9_.]|[\uac00-\ud7af]|[\u1100-\u11ff]|[\u3130-\u318f]|[\ua960-\ua97f]|[\ud7b0-\ud7ff])+$/i,
};

export function getBrowserTimezone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch {
    return "Asia/Seoul";
  }
}
