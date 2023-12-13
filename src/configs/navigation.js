import { createRef, lazy } from 'react';

import i18n from 'configs/i18n';

const Arbitrage = lazy(() => import('pages/Arbitrage'));
const Home = lazy(() => import('pages/Home'));
// const Investment = lazy(() => import('pages/Investment'));
const Login = lazy(() => import('pages/Login'));
const MyPage = lazy(() => import('pages/MyPage'));
const News = lazy(() => import('pages/News'));
const Register = lazy(() => import('pages/Register'));

const main = [
  {
    index: true,
    name: 'home',
    path: '/',
    element: Home,
    displayChat: true,
    displayTicker: true,
    getTitle: () => i18n.t('Home'),
    ref: createRef(),
  },
  {
    name: 'arbitrage',
    path: '/arbitrage',
    element: Arbitrage,
    displayChat: true,
    getTitle: () => i18n.t('Arbitrage'),
    ref: createRef(),
  },
  // {
  //   name: 'investment',
  //   path: '/investment',
  //   element: Investment,
  //   displayChat: true,
  //   getTitle: () => i18n.t('Investment'),
  //   ref: createRef(),
  // },
  {
    name: 'news',
    path: '/news',
    element: News,
    displayChat: true,
    getTitle: () => i18n.t('News'),
    ref: createRef(),
  },
];

const protectedRoutes = [
  {
    name: 'my-page',
    path: '/my-page',
    element: MyPage,
    getTitle: () => i18n.t('My Page'),
    ref: createRef(),
  },
];

const publicRoutes = [
  {
    name: 'login',
    path: '/login',
    element: Login,
    getTitle: () => i18n.t('Login'),
    ref: createRef(),
  },
  {
    name: 'register',
    path: '/register',
    element: Register,
    getTitle: () => i18n.t('Register'),
    ref: createRef(),
  },
];

export default {
  main,
  protectedRoutes,
  publicRoutes,
};
export const routes = main.concat(publicRoutes, protectedRoutes);
