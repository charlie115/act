/* eslint-disable prefer-template */
import isUndefined from 'lodash/isUndefined';

import i18n from 'configs/i18n';

export default (number, decimal = 0, min = 0) => {
  const pos = Math.abs(number);

  let maximumFractionDigits = decimal;

  if (pos < 1) {
    const leadingZeros = -Math.floor(Math.log10(pos) + 1);
    if (leadingZeros >= 4) maximumFractionDigits = 9;
    else maximumFractionDigits = isUndefined(decimal) ? 3 : decimal;
  }

  return number
    ? i18n.t('intlNumber', {
        value: number, // Number(Math.round(number + 'e' + 5) + 'e-5'),
        minimumFractionDigits: min,
        maximumFractionDigits,
      })
    : number;
};
