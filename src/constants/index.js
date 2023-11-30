export const DATE_FORMAT_API_QUERY = "yyyy-MM-dd'T'HH:mm:ss";

export const DATE_FORMAT_BY_UNIT = {
  minutes: 'HH:mm',
  hours: 'HH:mm',
};

export const REGEX = {
  chatMention: /\B@([\w_]+)/,
  // eslint-disable-next-line no-control-regex
  ctrlCharactersRegex: /[\u0000-\u001F\u007F-\u009F\u2000-\u200D\uFEFF]/gim,
  spotMarketSuffix: /(_SPOT\/)([A-Z]+)/,
};
