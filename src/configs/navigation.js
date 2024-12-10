import { createRef, lazy } from 'react';

import { Navigate } from 'react-router-dom';

import HomeIcon from '@mui/icons-material/Home';
import FeedIcon from '@mui/icons-material/Feed';
import ForumIcon from '@mui/icons-material/Forum';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import SyncIcon from '@mui/icons-material/Sync';

import i18n from 'configs/i18n';

const Arbitrage = lazy(() => import('pages/arbitrage'));
const AvgFundingRate = lazy(() => import('pages/arbitrage/AvgFundingRate'));
const FundingRateDiff = lazy(() => import('pages/arbitrage/FundingRateDiff'));

const APIKey = lazy(() => import('pages/bot/APIKey'));
const Bot = lazy(() => import('pages/bot'));
const Deposit = lazy(() => import('pages/bot/Deposit'));
const Position = lazy(() => import('pages/bot/Position'));
const Capital = lazy(() => import('pages/bot/Capital'));
const PnLHistory = lazy(() => import('pages/bot/PnLHistory'));
const Settings = lazy(() => import('pages/bot/Settings'));
const Triggers = lazy(() => import('pages/bot/Triggers'));

const Home = lazy(() => import('pages/Home'));
// const Investment = lazy(() => import('pages/Investment'));
const Login = lazy(() => import('pages/Login'));
const MyPage = lazy(() => import('pages/MyPage'));
const News = lazy(() => import('pages/News'));
const Register = lazy(() => import('pages/Register'));

const CommunityBoard = lazy(() => import('pages/community-board'));
const CommunityBoardPost = lazy(() =>
  import('pages/community-board/CommunityBoardPost')
);
const CommunityBoardPostNew = lazy(() =>
  import('pages/community-board/CommunityBoardPostNew')
);

const main = [
  {
    index: true,
    name: 'home',
    path: '/',
    element: Home,
    displayChat: true,
    displayInHeader: true,
    displayTicker: true,
    icon: HomeIcon,
    getTitle: () => i18n.t('Home'),
    ref: createRef(),
  },
  {
    name: 'arbitrage',
    path: '/arbitrage',
    element: Arbitrage,
    displayChat: true,
    displayInHeader: true,
    icon: SyncIcon,
    getTitle: () => i18n.t('Arbitrage'),
    ref: createRef(),
    children: [
      {
        name: 'arbitrage-funding-rate-diff',
        path: '/arbitrage/funding-rate/diff',
        element: FundingRateDiff,
      },
      {
        name: 'arbitrage-avg-funding-rate',
        path: '/arbitrage/funding-rate/avg',
        element: AvgFundingRate,
      },
      {
        index: true,
        name: '/arbitrage',
        path: '/arbitrage',
        element: Navigate,
        elementProps: { replace: true, to: '/arbitrage/funding-rate/diff' },
      },
    ],
  },
  {
    name: 'community-board',
    path: '/community-board',
    element: CommunityBoard,
    displayChat: true,
    displayInHeader: true,
    icon: ForumIcon,
    getTitle: () => i18n.t('Notice Board'),
    ref: createRef(),
    children: [
      {
        name: 'community-board-new',
        path: '/community-board/post/new',
        element: CommunityBoardPostNew,
      },
      {
        name: 'community-board-post',
        path: '/community-board/post/:postId',
        element: CommunityBoardPost,
      },
    ],
  },
  {
    name: 'news',
    path: '/news',
    element: News,
    displayChat: true,
    displayInHeader: true,
    icon: FeedIcon,
    getTitle: () => i18n.t('News'),
    ref: createRef(),
  },
  {
    name: 'bot',
    path: '/bot',
    element: Bot,
    displayChat: true,
    displayInHeader: true,
    icon: SmartToyIcon,
    getTitle: () => i18n.t('Bot'),
    ref: createRef(),
    children: [
      {
        name: 'bot-triggers',
        path: '/bot/triggers',
        element: Triggers,
      },
      {
        name: 'bot/pnl-history',
        path: '/bot/pnl-history',
        element: PnLHistory,
      },
      {
        name: 'bot/position',
        path: '/bot/position',
        element: Position,
      },
      {
        name: 'bot/capital',
        path: '/bot/capital',
        element: Capital,
      },
      {
        name: 'bot/settings',
        path: '/bot/settings',
        element: Settings,
      },
      {
        name: 'bot/api-key',
        path: '/bot/api-key',
        element: APIKey,
      },
      {
        name: 'bot/deposit',
        path: '/bot/deposit',
        element: Deposit,
      },
      {
        index: true,
        name: '/bot',
        path: '/bot',
        element: Navigate,
        elementProps: { replace: true, to: '/bot/triggers' },
      },
    ],
  },
];

const protectedRoutes = [
  {
    name: 'my-page',
    path: '/my-page',
    element: MyPage,
    displayChat: true,
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
