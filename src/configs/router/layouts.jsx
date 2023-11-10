import React, { forwardRef, useEffect, useMemo } from 'react';

import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { CSSTransition, SwitchTransition } from 'react-transition-group';

import { Helmet } from 'react-helmet';

import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import IconButton from '@mui/material/IconButton';
import LinearProgress from '@mui/material/LinearProgress';
import Paper from '@mui/material/Paper';
import Snackbar from '@mui/material/Snackbar';

import KeyboardArrowUpRoundedIcon from '@mui/icons-material/KeyboardArrowUpRounded';

import { useDispatch, useSelector } from 'react-redux';
import { useUserQuery } from 'redux/api/drf/auth';
import { setSnackbar } from 'redux/reducers/app';

import { useTranslation } from 'react-i18next';

import { useWindowScroll } from '@uidotdev/usehooks';

import { routes } from 'configs/navigation';

import ChatWidget from 'components/chat_widget/ChatWidget';
import Header from 'components/Header';

const SnackbarAlert = forwardRef((props, ref) => (
  <Alert ref={ref} elevation={6} {...props} />
));

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
  const dispatch = useDispatch();
  const location = useLocation();
  const { i18n } = useTranslation();

  const [{ y }, scrollTo] = useWindowScroll();

  const currentRoute = useMemo(
    () => routes.find((route) => route.path === location.pathname),
    [location.pathname, i18n.language]
  );

  const { loggedin } = useSelector((state) => state.auth);
  const { snackbar } = useSelector((state) => state.app);

  useUserQuery({}, { skip: !loggedin });

  useEffect(() => {
    scrollTo({ left: 0, top: 0, behavior: 'smooth' });
  }, [location.pathname]);

  const onSnackbarClose = () => {
    dispatch(setSnackbar({}));
    if (snackbar?.closeCallback) snackbar.closeCallback();
  };

  return (
    <>
      <Helmet>
        <title>{currentRoute.getTitle()} — Ar-Kimp</title>
      </Helmet>
      <Snackbar
        autoHideDuration={6000}
        open={false}
        onClose={onSnackbarClose}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        {...snackbar?.snackbarProps}
      >
        <SnackbarAlert
          onClose={onSnackbarClose}
          severity="info"
          sx={{ width: '100%' }}
          {...snackbar?.alertProps}
        >
          {snackbar?.message}
        </SnackbarAlert>
      </Snackbar>
      <Box>
        <Header />
        <Box sx={{ mb: 4, p: 1 }}>
          <React.Suspense fallback={<LinearProgress />}>
            <TVTickerWidget isVisible={currentRoute.displayTicker} />
          </React.Suspense>
          <Grid container ref={currentRoute.ref} spacing={1}>
            <Grid item xs={12} lg={2}>
              <Box
                component={Paper}
                sx={{
                  p: 1,
                  textAlign: 'center',
                  minHeight: { xs: '22.5vh', lg: '90vh' },
                }}
              >
                AD???
              </Box>
            </Grid>
            <Grid
              item
              xs={12}
              lg={8}
              sx={{
                display: 'flex',
                minHeight: { xs: '45vh', lg: '90vh' },
                position: 'relative',
              }}
            >
              <Box
                component={Paper}
                sx={{ display: 'flex', flex: 1, overflowX: 'clip' }}
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
            <Grid item xs={12} lg={2}>
              <Box
                component={Paper}
                sx={{
                  p: 1,
                  textAlign: 'center',
                  minHeight: { xs: '22.5vh', lg: '90vh' },
                }}
              >
                AD???
              </Box>
            </Grid>
          </Grid>
        </Box>
        {y > 500 && (
          <Box
            sx={{
              position: 'fixed',
              bottom: 15,
              right: '50%',
              transform: 'translateX(50%)',
              zIndex: 1501,
            }}
          >
            <IconButton
              size="medium"
              onClick={() => scrollTo({ left: 0, top: 0, behavior: 'smooth' })}
              sx={{ bgcolor: 'grey.900', color: 'light.main' }}
            >
              <KeyboardArrowUpRoundedIcon fontSize="large" />
            </IconButton>
          </Box>
        )}
        <ChatWidget isVisible={currentRoute.displayChat} />
      </Box>
    </>
  );
}
