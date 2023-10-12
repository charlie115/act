/* eslint-disable no-bitwise */
import isNumber from 'lodash/isNumber';

import i18n from 'configs/i18n';

const SHORT_NUMBER_SYMBOL = {
  en: ['', 'K', 'M', 'B', 'T', 'T', 'T', 'T', 'T'],
  ko: ['', '', '', '천', '만', '만', '만', '만', '억'],
  zh: ['', 'K', 'M', 'B', 'T', 'T', 'T', 'T', 'T'],
};

export default (num, decimal, lang) => {
  if (!isNumber(num)) return num;
  if (num < 0) return 'N/A';

  const language = lang || i18n.language;

  const symbols = SHORT_NUMBER_SYMBOL[language];
  const dec = decimal || 0;
  const number = num;

  let tier;
  let scale;
  if (language === 'ko') {
    tier = Math.log10(Math.abs(number)) | 0;
    tier = Math.min(tier, 8);
    if (tier < 3) return number.toFixed(dec) * 1;
    scale = 10 ** tier;
  } else {
    tier = (Math.log10(Math.abs(number)) / 3) | 0;
    if (tier === 0) return number.toFixed(dec) * 1;
    scale = 10 ** (tier * 3);
  }

  const suffix = symbols[tier];
  const scaled = number / scale;
  const value = Math.floor(scaled * 10 ** dec) / 10 ** dec;
  return `${value}${suffix}`;
};
