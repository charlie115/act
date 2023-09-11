import React, { useMemo } from 'react';

import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { CSSTransition, SwitchTransition } from 'react-transition-group';

import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import LinearProgress from '@mui/material/LinearProgress';
import Paper from '@mui/material/Paper';

import { useSelector } from 'react-redux';

import Header from 'components/Header';

import { routes } from 'configs/navigation';

const TVTickerWidget = React.lazy(() =>
  import('components/trading_view/TVTickerWidget')
);

const WITH_TICKER_WIDGET_LOCATIONS = ['/'];

export function ProtectedLayout() {
  const token = useSelector((state) => state.auth.token);

  const location = useLocation();

  if (!token)
    return <Navigate to="/login" replace state={{ from: location }} />;

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

  const currentRoute = useMemo(
    () => routes.find((route) => route.path === location.pathname),
    [location.pathname]
  );

  return (
    <Box>
      <Header />
      <Box sx={{ mb: 4, p: 1 }}>
        <React.Suspense fallback={<LinearProgress />}>
          <TVTickerWidget isVisible={currentRoute.displayTicker} />
        </React.Suspense>
        <SwitchTransition>
          <CSSTransition
            key={location.pathname}
            nodeRef={currentRoute.ref}
            timeout={300}
            classNames="page"
            unmountOnExit
          >
            {() => (
              <Grid container ref={currentRoute.ref} spacing={1}>
                <Grid item xs={12} md={2}>
                  <Box
                    component={Paper}
                    sx={{ p: 1, textAlign: 'center', minHeight: 120 }}
                  >
                    AD???
                  </Box>
                </Grid>
                <Grid item xs={12} md={8} sx={{ display: 'flex' }}>
                  <Box
                    component={Paper}
                    sx={{
                      display: 'flex',
                      flex: 1,
                      p: 1,
                      minHeight: window.innerHeight - 150,
                    }}
                  >
                    <Outlet />
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
            )}
          </CSSTransition>
        </SwitchTransition>
      </Box>
    </Box>
  );
}
