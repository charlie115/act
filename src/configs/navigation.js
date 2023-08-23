import i18n from 'configs/i18n';

const main = [
  {
    name: 'home',
    path: '/',
    getTitle: () => i18n.t('Home'),
  },
  {
    name: 'arbitrage',
    path: '/arbitrage',
    getTitle: () => i18n.t('Arbitrage'),
  },
  {
    name: 'investment',
    path: '/investment',
    getTitle: () => i18n.t('Investment'),
  },
  { name: 'news', path: '/news', getTitle: () => i18n.t('News') },
];
// const settings = [{ path: '/', name: 'home', title: '홈' }];

export default {
  main,
  //
};
