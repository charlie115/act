import i18n from 'configs/i18n';

import BinanceSvg from 'assets/svg/binance.svg';
import BithumbSvg from 'assets/svg/bithumb.svg';
import BybitSvg from 'assets/svg/bybit.svg';
import OkxSvg from 'assets/svg/okx.svg';
import UPbitSvg from 'assets/svg/upbit.svg';

export const EXCHANGE_LIST = [
  {
    getLabel: () => i18n.t('UPbit'),
    value: 'UPBIT',
    icon: UPbitSvg,
  },
  {
    getLabel: () => i18n.t('Bithumb'),
    value: 'BITHUMB',
    icon: BithumbSvg,
  },
  {
    getLabel: () => i18n.t('Binance'),
    value: 'BINANCE',
    icon: BinanceSvg,
  },
  {
    getLabel: () => i18n.t('Bybit'),
    value: 'BYBIT',
    icon: BybitSvg,
  },
  {
    getLabel: () => i18n.t('OKX'),
    value: 'OKX',
    icon: OkxSvg,
  },
];

export const KLINE_DATA_TYPE = [
  {
    getKimpLabel: () => i18n.t('KIMP'),
    getTetherLabel: () => i18n.t('Tether'),
    label: 'TP',
    value: 'tp',
  },
  {
    getKimpLabel: () => i18n.t('Enter KIMP'),
    getTetherLabel: () => i18n.t('Enter Tether'),
    label: 'LS',
    value: 'LS',
  },
  {
    getKimpLabel: () => i18n.t('Exit KIMP'),
    getTetherLabel: () => i18n.t('Exit Tether'),
    label: 'SL',
    value: 'SL',
  },
];

export const INTERVAL_LIST = [
  {
    getLabel: () => i18n.t('{{value}}m', { value: 1 }),
    value: '1T',
    quantity: 1,
    unit: 'minutes',
  },
  // { getLabel: () => i18n.t('{{value}}m', { value: 3 }), value: '3T' },
  {
    getLabel: () => i18n.t('{{value}}m', { value: 5 }),
    value: '5T',
    quantity: 5,
    unit: 'minutes',
  },
  {
    getLabel: () => i18n.t('{{value}}m', { value: 15 }),
    value: '15T',
    quantity: 15,
    unit: 'minutes',
  },
  {
    getLabel: () => i18n.t('{{value}}m', { value: 30 }),
    value: '30T',
    quantity: 30,
    unit: 'minutes',
  },
  {
    getLabel: () => i18n.t('{{value}}h', { value: 1 }),
    value: '1H',
    quantity: 1,
    unit: 'hours',
  },
  {
    getLabel: () => i18n.t('{{value}}h', { value: 4 }),
    value: '4H',
    quantity: 4,
    unit: 'hours',
  },
  {
    getLabel: () => i18n.t('{{value}}D', { value: 1 }),
    value: '1D',
    quantity: 1,
    unit: 'days',
  },
];

export const MARKET_CODE_LIST = [
  {
    getLabel: () => i18n.t('UPbit'),
    value: 'UPBIT_SPOT/KRW',
    exchange: 'UPBIT',
    icon: UPbitSvg,
  },
  {
    getLabel: () => i18n.t('UPbit (BTC)'),
    value: 'UPBIT_SPOT/BTC',
    exchange: 'UPBIT',
    icon: UPbitSvg,
  },
  {
    getLabel: () => i18n.t('Bithumb'),
    value: 'BITHUMB_SPOT/KRW',
    exchange: 'BITHUMB',
    icon: BithumbSvg,
  },
  {
    getLabel: () => i18n.t('Bithumb (BTC)'),
    value: 'BITHUMB_SPOT/BTC',
    exchange: 'BITHUMB',
    icon: BithumbSvg,
  },
  {
    getLabel: () => i18n.t('Binance (USDT)'),
    value: 'BINANCE_SPOT/USDT',
    exchange: 'BINANCE',
    icon: BinanceSvg,
  },
  {
    getLabel: () => i18n.t('Binance (BTC)'),
    value: 'BINANCE_SPOT/BTC',
    exchange: 'BINANCE',
    icon: BinanceSvg,
  },
  {
    getLabel: () => i18n.t('Binance (BUSD)'),
    value: 'BINANCE_SPOT/BUSD',
    exchange: 'BINANCE',
    icon: BinanceSvg,
  },
  {
    getLabel: () => i18n.t('Binance USDⓈ-M (USDT)'),
    value: 'BINANCE_USD_M/USDT',
    exchange: 'BINANCE',
    icon: BinanceSvg,
  },
  {
    getLabel: () => i18n.t('Binance USDⓈ-M (BUSD)'),
    value: 'BINANCE_USD_M/BUSD',
    exchange: 'BINANCE',
    icon: BinanceSvg,
  },
  {
    getLabel: () => i18n.t('Binance COIN-M (USD)'),
    value: 'BINANCE_COIN_M/USD',
    exchange: 'BINANCE',
    icon: BinanceSvg,
  },
  {
    getLabel: () => i18n.t('Bybit (KRW)'),
    value: 'BYBIT_SPOT/KRW',
    exchange: 'BYBIT',
    icon: BybitSvg,
  },
  {
    getLabel: () => i18n.t('Bybit USDⓈ-M (USDT)'),
    value: 'BYBIT_USD_M/USDT',
    exchange: 'BYBIT',
    icon: BybitSvg,
  },
  {
    getLabel: () => i18n.t('Bybit COIN-M (USD)'),
    value: 'BYBIT_COIN_M/USD',
    exchange: 'BYBIT',
    icon: BybitSvg,
  },
  {
    getLabel: () => i18n.t('OKX (USDT)'),
    value: 'OKX_SPOT/USDT',
    exchange: 'OKX',
    icon: OkxSvg,
  },
  {
    getLabel: () => i18n.t('OKX USDⓈ-M (USDT)'),
    value: 'OKX_USD_M/USDT',
    exchange: 'OKX',
    icon: OkxSvg,
  },
  {
    getLabel: () => i18n.t('OKX COIN-M (USD)'),
    value: 'OKX_COIN_M/USD',
    exchange: 'OKX',
    icon: OkxSvg,
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
