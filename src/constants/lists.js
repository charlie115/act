import i18n from 'configs/i18n';
import formatShortNumber from 'utils/formatShortNumber';

const DEFAULT_FIELD_PROPS = {
  hasTooltip: true,
  cellProps: { align: 'right', fontSize: 8 },
  headerProps: { align: 'right', width: '14%' },
  headerStackStyle: { alignItems: 'center', justifyContent: 'end' },
  stackStyle: { justifyContent: 'end' },
  formatValue: (value) =>
    value
      ? i18n.t('intlNumber', {
          value: Math.round((value + Number.EPSILON) * 1000) / 1000,
        })
      : '',
};

export const COIN_FIELDS = [
  {
    fieldKey: 'name',
    getLabel: () => i18n.t('Name'),
    headerProps: { width: '10%' },
    headerStackStyle: { alignItems: 'center' },
    cellProps: { align: 'left' },
  },
  {
    fieldKey: 'price',
    getLabel: () => i18n.t('Price'),
    ...DEFAULT_FIELD_PROPS,
  },
  { fieldKey: 'kimp', getLabel: () => i18n.t('KIMP'), ...DEFAULT_FIELD_PROPS },
  {
    fieldKey: 'change',
    getLabel: () => i18n.t('Change'),
    ...DEFAULT_FIELD_PROPS,
  },
  {
    fieldKey: 'weekhigh',
    getLabel: () => i18n.t('52-Week High'),
    ...DEFAULT_FIELD_PROPS,
  },
  {
    fieldKey: 'weeklow',
    getLabel: () => i18n.t('52-Week Low'),
    ...DEFAULT_FIELD_PROPS,
  },
  {
    fieldKey: 'volume',
    getLabel: () => i18n.t('Volume'),
    ...DEFAULT_FIELD_PROPS,
    formatValue: (value) => formatShortNumber(value, 1),
  },
];

export const DATA_INTERVALS = [
  { getLabel: () => i18n.t('{{value}}m', { value: 1 }), value: '1m' },
  { getLabel: () => i18n.t('{{value}}m', { value: 3 }), value: '3m' },
  { getLabel: () => i18n.t('{{value}}m', { value: 5 }), value: '5m' },
  { getLabel: () => i18n.t('{{value}}m', { value: 15 }), value: '15m' },
  { getLabel: () => i18n.t('{{value}}m', { value: 30 }), value: '30m' },
  { getLabel: () => i18n.t('{{value}}h', { value: 1 }), value: '1h' },
  { getLabel: () => i18n.t('{{value}}h', { value: 4 }), value: '4h' },
  { getLabel: () => i18n.t('Day'), value: 'day' },
  { getLabel: () => i18n.t('Week'), value: 'week' },
  { getLabel: () => i18n.t('Month'), value: 'month' },
];

export const TRADING_COMPANIES = [
  { getLabel: () => i18n.t('Binance'), value: 'BINANCE', currency: 'USDT' },
  { getLabel: () => i18n.t('UPbit'), value: 'UPBIT', currency: 'KRW' },
  { getLabel: () => i18n.t('KIMP'), value: 'KIMP', currency: 'KRW' },
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
