import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import CheckBoxIcon from '@mui/icons-material/CheckBox';
import NotificationsIcon from '@mui/icons-material/Notifications';

import i18n from 'configs/i18n';
import colors from 'configs/theme/colors';

import BinanceSvg from 'assets/svg/binance.svg';
import BithumbSvg from 'assets/svg/bithumb.svg';
import BybitSvg from 'assets/svg/bybit.svg';
import OkxSvg from 'assets/svg/okx.svg';
import UPbitSvg from 'assets/svg/upbit.svg';

export const CHART_DATA_TYPE = [
  {
    getKimpLabel: () => i18n.t('KIMP'),
    getTetherLabel: () => i18n.t('Tether'),
    getLabel: () => 'TP',
    label: 'TP',
    value: 'tp',
  },
  {
    getKimpLabel: () => i18n.t('Enter KIMP'),
    getTetherLabel: () => i18n.t('Enter Tether'),
    getLabel: () => 'LS',
    label: 'LS',
    value: 'LS',
  },
  {
    getKimpLabel: () => i18n.t('Exit KIMP'),
    getTetherLabel: () => i18n.t('Exit Tether'),
    getLabel: () => 'SL',
    label: 'SL',
    value: 'SL',
  },
  {
    getKimpLabel: () => i18n.t('Funding Rate'),
    getTetherLabel: () => i18n.t('Funding Rate'),
    getLabel: () => i18n.t('Funding Rate'),
    value: 'FR',
  },
  {
    getKimpLabel: () => i18n.t('Funding Rate Difference'),
    getTetherLabel: () => i18n.t('Funding Rate Difference'),
    getLabel: () => i18n.t('Funding Rate Difference'),
    value: 'FRD',
  },
  {
    getKimpLabel: () => i18n.t('Avg Funding Rate Difference'),
    getTetherLabel: () => i18n.t('Avg Funding Rate Difference'),
    getLabel: () => i18n.t('Avg Funding Rate Difference'),
    value: 'AFRD',
  },
];

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
  // {
  //   getLabel: () => i18n.t('{{value}}D', { value: 1 }),
  //   value: '1D',
  //   quantity: 1,
  //   unit: 'days',
  // },
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
    getLabel: () => i18n.t('Bybit (USDT)'),
    value: 'BYBIT_SPOT/USDT',
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

export const PERIOD_LIST = [
  { value: 'day', getLabel: () => i18n.t('Daily') },
  { value: 'week', getLabel: () => i18n.t('Weekly') },
  { value: 'month', getLabel: () => i18n.t('Monthly') },
];

export const POST_CATEGORY_LIST = [
  {
    color: colors.error.main,
    value: 'Announcement',
    getLabel: () => i18n.t('Announcement'),
  },
  {
    color: colors.purple['600'],
    value: 'Freewriting',
    getLabel: () => i18n.t('Freewriting'),
  },
  {
    color: colors.accent.main,
    value: 'Question',
    getLabel: () => i18n.t('Question'),
  },
  {
    color: colors.teal['600'],
    value: 'Investment Strategy',
    getLabel: () => i18n.t('Investment Strategy'),
  },
  {
    color: colors.info.main,
    value: 'Information',
    getLabel: () => i18n.t('Information'),
  },
  {
    color: colors.cyan['600'],
    value: 'User Guide',
    getLabel: () => i18n.t('User Guide'),
  },
];

export const TRADING_VIEW_TICKER_SYMBOLS = [
  {
    description: '달러',
    proName: 'FX_IDC:USDKRW',
  },
  {
    description: '테더',
    proName: 'USDTKRW',
  },
  {
    description: 'BTC도미넌스',
    proName: 'CRYPTOCAP:BTC.D',
  },
  {
    description: '비트코인',
    proName: 'BINANCE:BTCUSDT',
  },
  {
    description: '나스닥',
    proName: 'FOREXCOM:NSXUSD',
  },
];

export const TRIGGER_LIST = [
  {
    getLabel: () => i18n.t('All'),
    value: 'ALL',
    icon: CheckBoxIcon,
    tabId: 2,
  },
  {
    getLabel: () => i18n.t('Alarms'),
    value: 'alarms',
    icon: NotificationsIcon,
    tabId: 0,
  },
  {
    getLabel: () => i18n.t('Auto Trade'),
    value: 'autoTrade',
    icon: AccountBalanceWalletIcon,
    tabId: 1,
  },
];
