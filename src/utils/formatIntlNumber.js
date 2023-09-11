/* eslint-disable prefer-template */
import i18n from "configs/i18n";

export default (number, decimals = 2) =>
  number
    ? i18n.t("intlNumber", {
        value: number, // Number(Math.round(number + 'e' + 5) + 'e-5'),
        minimumFractionDigits: decimals,
      })
    : number;
