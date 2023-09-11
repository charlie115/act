import isNumber from 'lodash/isNumber';

import i18n from 'configs/i18n';

const SHORT_NUMBER_SYMBOL = {
  en: ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y'],
  ko: ['', '천', '만', 'G', 'T', 'P', 'E', 'Z', 'Y'],
  zh: ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y'],
};

export default (num, decimal, lang) => {
  if (!isNumber(num)) return num;
  if (num < 0) return 'N/A';

  const language = lang || i18n.language;

  const symbols = SHORT_NUMBER_SYMBOL[language];
  const dec = decimal || 0;
  const number = num;
  // eslint-disable-next-line no-bitwise
  const tier = (Math.log10(Math.abs(number)) / 3) | 0;

  if (tier === 0) return number.toFixed(dec) * 1;

  const suffix = symbols[tier];
  const scale = 10 ** (tier * 3); // Math.pow(10, tier * 3);
  const scaled = number / scale;

  const value = Math.floor(scaled * 10 ** dec) / 10 ** dec;
  return `${value}${suffix}`;
};
