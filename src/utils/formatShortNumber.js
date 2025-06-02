/* eslint-disable no-bitwise */
import isNumber from 'lodash/isNumber';

import i18n from 'configs/i18n';

const SHORT_NUMBER_SYMBOL = {
  en: ['', 'K', 'M', 'B', 'T', 'T', 'T', 'T', 'T'],
  ko: ['', '', '', '천', '만', '십만', '백만', '천만', '억'],
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
    // Only use 만(10,000), 백만(1,000,000), 억(100,000,000)
    if (number < 10000) {
      return number.toFixed(dec) * 1;
    }
    if (number < 1000000) {
      scale = 10000;
      tier = 4; // 만
    } else if (number < 100000000) {
      scale = 1000000;
      tier = 6; // 백만
    } else {
      scale = 100000000;
      tier = 8; // 억
    }
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
