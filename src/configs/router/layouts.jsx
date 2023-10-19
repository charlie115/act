import React, { useMemo } from 'react';

import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { CSSTransition, SwitchTransition } from 'react-transition-group';

import { Helmet } from 'react-helmet';

import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import LinearProgress from '@mui/material/LinearProgress';
import Paper from '@mui/material/Paper';

import { useSelector } from 'react-redux';
import { useUserQuery } from 'redux/api/drf/auth';

import { useTranslation } from 'react-i18next';

import { routes } from 'configs/navigation';

import ChatWidget from 'components/chat_widget/ChatWidget';
import Header from 'components/Header';

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

export function MainLayout() {
  const location = useLocation();
  const { i18n } = useTranslation();

  const currentRoute = useMemo(
    () => routes.find((route) => route.path === location.pathname),
    [location.pathname, i18n.language]
  );

  const { loggedin } = useSelector((state) => state.auth);

  useUserQuery({}, { skip: !loggedin });

  return (
    <>
      <Helmet>
        <title>{currentRoute.getTitle()} — Ar-Kimp</title>
      </Helmet>
      <Box>
        <Header />
        <Box sx={{ mb: 4, p: 1 }}>
          <React.Suspense fallback={<LinearProgress />}>
            <TVTickerWidget isVisible={currentRoute.displayTicker} />
          </React.Suspense>
          <Grid container ref={currentRoute.ref} spacing={1}>
            <Grid item xs={12} md={2}>
              <Box
                component={Paper}
                sx={{ p: 1, textAlign: 'center', minHeight: 120 }}
              >
                AD???
              </Box>
            </Grid>
            <Grid
              item
              xs={12}
              md={8}
              sx={{ display: 'flex', minHeight: window.innerHeight - 100 }}
            >
              <Box
                component={Paper}
                sx={{
                  display: 'flex',
                  flex: 1,
                  p: 1,
                }}
              >
                <SwitchTransition>
                  <CSSTransition
                    unmountOnExit
                    key={location.pathname}
                    nodeRef={currentRoute.ref}
                    timeout={3000}
                    classNames="pages"
                  >
                    {() => <Outlet />}
                  </CSSTransition>
                </SwitchTransition>
              </Box>
            </Grid>
            <Grid item xs={12} md={2}>
              <Box
                component={Paper}
                sx={{ p: 1, textAlign: 'center', minHeight: 120 }}
              >
                AD???
              </Box>
            </Grid>
          </Grid>
        </Box>
        <ChatWidget isVisible={currentRoute.displayChat} />
      </Box>
    </>
  );
}
