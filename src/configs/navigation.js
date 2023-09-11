import React, { createRef, lazy } from 'react';

import i18n from 'configs/i18n';

const Arbitrage = lazy(() => import('pages/Arbitrage'));
const Home = lazy(() => import('pages/Home'));
const Login = lazy(() => import('pages/Login'));

const main = [
  {
    index: true,
    name: 'home',
    path: '/',
    element: Home,
    displayTicker: true,
    getTitle: () => i18n.t('Home'),
    ref: createRef(),
  },
  {
    name: 'arbitrage',
    path: '/arbitrage',
    element: Arbitrage,
    getTitle: () => i18n.t('Arbitrage'),
    ref: createRef(),
  },
  {
    name: 'investment',
    path: '/investment',
    element: Arbitrage,
    getTitle: () => i18n.t('Investment'),
    ref: createRef(),
  },
  {
    name: 'news',
    path: '/news',
    element: Arbitrage,
    getTitle: () => i18n.t('News'),
    ref: createRef(),
  },
];

const publicRoutes = [
  {
    name: 'login',
    path: '/login',
    element: Login,
    getTitle: () => i18n.t('News'),
    ref: createRef(),
  },
];

export default {
  main,
  publicRoutes,
};
export const routes = main.concat(publicRoutes);
