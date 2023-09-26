import i18n from 'configs/i18n';

import { ReactComponent as BinanceSvg } from 'assets/svg/binance.svg';
import { ReactComponent as UPbitSvg } from 'assets/svg/upbit.svg';

export const COIN_KLINE_DATA = [
  { label: 'TP', value: 'tp' },
  { label: 'LS', value: 'LS' },
  { label: 'SL', value: 'SL' },
];

export const INTERVAL_LIST = [
  { getLabel: () => i18n.t('{{value}}m', { value: 1 }), value: '1T' },
  // { getLabel: () => i18n.t('{{value}}m', { value: 3 }), value: '3T' },
  { getLabel: () => i18n.t('{{value}}m', { value: 5 }), value: '5T' },
  { getLabel: () => i18n.t('{{value}}m', { value: 15 }), value: '15T' },
  { getLabel: () => i18n.t('{{value}}m', { value: 30 }), value: '30T' },
  { getLabel: () => i18n.t('{{value}}h', { value: 1 }), value: '1H' },
  { getLabel: () => i18n.t('{{value}}h', { value: 4 }), value: '4H' },
  { getLabel: () => i18n.t('{{value}}D', { value: 1 }), value: 'day' },
  { getLabel: () => i18n.t('{{value}}W', { value: 1 }), value: 'week' },
  { getLabel: () => i18n.t('{{value}}M', { value: 1 }), value: 'month' },
];

export const MARKET_CODE_LIST = [
  { getLabel: () => i18n.t('UPbit'), value: 'UPBIT_SPOT/KRW', icon: UPbitSvg },
  {
    getLabel: () => i18n.t('UPbit (BTC)'),
    value: 'UPBIT_SPOT/BTC',
    icon: UPbitSvg,
  },
  {
    getLabel: () => i18n.t('Binance (USDT)'),
    value: 'BINANCE_SPOT/USDT',
    icon: BinanceSvg,
  },
  {
    getLabel: () => i18n.t('Binance (BTC)'),
    value: 'BINANCE_SPOT/BTC',
    icon: BinanceSvg,
  },
  {
    getLabel: () => i18n.t('Binance (BUSD)'),
    value: 'BINANCE_SPOT/BUSD',
    icon: BinanceSvg,
  },
  {
    getLabel: () => i18n.t('Binance USDⓈ-M (USDT)'),
    value: 'BINANCE_USD_M/USDT',
    icon: BinanceSvg,
  },
  {
    getLabel: () => i18n.t('Binance USDⓈ-M (BUSD)'),
    value: 'BINANCE_USD_M/BUSD',
    icon: BinanceSvg,
  },
  {
    getLabel: () => i18n.t('Binance COIN-M (USD)'),
    value: 'BINANCE_COIN_M/USD',
    icon: BinanceSvg,
  },
];

export const TRADING_VIEW_TICKER_SYMBOLS = [
  {
    description: '달러환율',
    proName: 'FX_IDC:USDKRW',
  },
  {
    description: '나스닥',
    proName: 'FOREXCOM:NSXUSD',
  },
  {
    description: 'S&P 500',
    proName: 'FOREXCOM:SPXUSD',
  },
  {
    description: 'BTC도미넌스',
    proName: 'CRYPTOCAP:BTC.D',
  },
  {
    description: '코스피',
    proName: 'KRX:KOSPI',
  },
  {
    // description: '코스닥',
    proName: 'KRX:KOSDAQ',
  },
];
