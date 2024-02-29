import React, { useEffect, useMemo, useRef, useState } from 'react';

import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { CSSTransition, SwitchTransition } from 'react-transition-group';

import { Helmet } from 'react-helmet';

import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Drawer from '@mui/material/Drawer';
import IconButton from '@mui/material/IconButton';
import LinearProgress from '@mui/material/LinearProgress';
import Paper from '@mui/material/Paper';

import List from '@mui/material/List';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import MenuIcon from '@mui/icons-material/Menu';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import InboxIcon from '@mui/icons-material/MoveToInbox';
import MailIcon from '@mui/icons-material/Mail';

import { alpha, styled, useTheme } from '@mui/material/styles';

import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';

import { useTranslation } from 'react-i18next';

import { useSelector } from 'react-redux';
import { useUserQuery, useUserPatchMutation } from 'redux/api/drf/auth';

import { logout } from 'redux/reducers/auth';

import useElementScroll from 'hooks/useElementScroll';

import { routes } from 'configs/navigation';

import ChatWidget, { DrawerHeader } from 'components/chat_widget';
// import ChatWidget from 'components/chat_widget/ChatWidget';
import Header from 'components/Header';

import { GlobalSnackbarProvider } from 'hooks/useGlobalSnackbar';

import { RIGHT_SIDEBAR_WIDTH } from 'constants';

export default function MainLayout() {
  const theme = useTheme();

  const location = useLocation();
  const { i18n } = useTranslation();

  const currentRoute = useMemo(
    () => routes.find((route) => route.path === location.pathname),
    [location.pathname, i18n.language]
  );

  const { loggedin, telegramBot, user } = useSelector((state) => state.auth);

  const { isError, isSuccess } = useUserQuery({}, { skip: !loggedin });
  const [patchUser] = useUserPatchMutation();

  const [open, setOpen] = useState(false);

  const [mainRef, { y }, scrollTo] = useElementScroll([user]);

  useEffect(() => {
    const handleContextmenu = (e) =>
      process.env.REACT_APP_ENV !== 'production' ? null : e.preventDefault();
    document.addEventListener('contextmenu', handleContextmenu);
    return () => {
      document.removeEventListener('contextmenu', handleContextmenu);
    };
  }, []);

  useEffect(() => {
    if (isError) logout();
  }, [isError]);

  useEffect(() => {
    if (isSuccess) {
      const telegram = user?.socialapps?.find((o) => o.provider === 'telegram');
      if (!telegram) patchUser({ telegram_bot: true });
    }
  }, [isSuccess, user?.socialapps]);

  useEffect(() => {
    scrollTo({ top: 0, behavior: 'smooth' });
  }, [location.pathname]);

  if (loggedin && !telegramBot && !user) return null;

  return (
    <>
      <Helmet>
        <title>{currentRoute.getTitle()} — Ar-Kimp</title>
      </Helmet>
      <GlobalSnackbarProvider>
        <Box sx={{ display: 'flex' }}>
          <NavAppBar position="fixed" open={open}>
            <Header />
          </NavAppBar>
          <Main ref={mainRef} open={open} sx={{ mb: 4, p: 1 }}>
            <DrawerHeader />
            <React.Suspense fallback={<LinearProgress />}>
              <TVTickerWidget isVisible={currentRoute.displayTicker} />
            </React.Suspense>
            <Box
              component={Paper}
              sx={{
                display: 'flex',
                flex: 1,
                overflowX: 'clip',
                minHeight: { xs: '45vh', lg: '90vh' },
                position: 'relative',
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
          </Main>
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
                onClick={() => scrollTo({ top: 0, behavior: 'smooth' })}
                sx={{ bgcolor: 'grey.900', color: 'light.main' }}
              >
                <KeyboardArrowUpIcon fontSize="large" />
              </IconButton>
            </Box>
          )}
          <ChatWidget
            isVisible={currentRoute.displayChat}
            onStateChange={(state) => setOpen(state.open)}
          />
        </Box>
      </GlobalSnackbarProvider>
    </>
  );
}

const Main = styled(Box, { shouldForwardProp: (prop) => prop !== 'open' })(
  ({ theme, open }) => ({
    flexGrow: 1,
    padding: theme.spacing(3),
    transition: theme.transitions.create('margin', {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen,
    }),
    marginRight: -RIGHT_SIDEBAR_WIDTH,
    ...(open && {
      transition: theme.transitions.create('margin', {
        easing: theme.transitions.easing.easeOut,
        duration: theme.transitions.duration.enteringScreen,
      }),
      marginRight: 0,
    }),
    height: '100vh',
    overflowY: 'auto',
    position: 'relative',
    scrollBehavior: 'smooth !important',
  })
);

const NavAppBar = styled(AppBar, {
  shouldForwardProp: (prop) => prop !== 'open',
})(({ theme, open }) => ({
  backgroundColor: theme.palette.dark.light,
  transition: theme.transitions.create(['margin', 'width'], {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  ...(open && {
    width: `calc(100% - ${RIGHT_SIDEBAR_WIDTH}px)`,
    transition: theme.transitions.create(['margin', 'width'], {
      easing: theme.transitions.easing.easeOut,
      duration: theme.transitions.duration.enteringScreen,
    }),
    marginRight: RIGHT_SIDEBAR_WIDTH,
  }),
}));

const TVTickerWidget = React.lazy(() =>
  import('components/trading_view/TVTickerWidget')
);
