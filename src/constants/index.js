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
  koreanCharacters:
    /[\uac00-\ud7af]|[\u1100-\u11ff]|[\u3130-\u318f]|[\ua960-\ua97f]|[\ud7b0-\ud7ff]$/i,
  usernameFirstCharacter:
    /^[A-Za-z]|[\uac00-\ud7af]|[\u1100-\u11ff]|[\u3130-\u318f]|[\ua960-\ua97f]|[\ud7b0-\ud7ff]/i,
  usernameFull:
    /^([A-Za-z0-9_.]|[\uac00-\ud7af]|[\u1100-\u11ff]|[\u3130-\u318f]|[\ua960-\ua97f]|[\ud7b0-\ud7ff])+$/i,
};
