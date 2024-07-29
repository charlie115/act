import React, { useEffect, useMemo } from 'react';

import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { CSSTransition, SwitchTransition } from 'react-transition-group';

import { Helmet } from 'react-helmet';

import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import LinearProgress from '@mui/material/LinearProgress';
import Paper from '@mui/material/Paper';

import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';

import { useSelector } from 'react-redux';
import { useUserQuery, useUserPatchMutation } from 'redux/api/drf/auth';

import { logout } from 'redux/reducers/auth';

import { useTranslation } from 'react-i18next';

import { useWindowScroll } from '@uidotdev/usehooks';

import { routes } from 'configs/navigation';

import ChatWidget from 'components/chat_widget/ChatWidget';
import Header from 'components/Header';

import { GlobalSnackbarProvider } from 'hooks/useGlobalSnackbar';

const TVTickerWidget = React.lazy(() =>
  import('components/trading_view/TVTickerWidget')
);

export function ProtectedLayout() {
  const loggedin = useSelector((state) => state.auth.loggedin);

  const location = useLocation();

  if (!loggedin)
    return <Navigate replace to="/login" state={{ from: location }} />;

  return <Outlet />;
}

export function PublicLayout() {
  const token = useSelector((state) => state.auth.token);

  const location = useLocation();

  if (token) return <Navigate to="/" replace state={{ from: location }} />;

  return <Outlet />;
}
