import React, { useEffect, useMemo, useState } from 'react';

import { Outlet, useLocation } from 'react-router-dom';

import { CSSTransition, SwitchTransition } from 'react-transition-group';

import SEO from 'components/SEO';

import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import LinearProgress from '@mui/material/LinearProgress';
import Paper from '@mui/material/Paper';
import Zoom from '@mui/material/Zoom';

import { styled, alpha, keyframes } from '@mui/material/styles';

import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';

import { useTranslation } from 'react-i18next';

import { useSelector } from 'react-redux';
import { useUserQuery, useUserPatchMutation } from 'redux/api/drf/auth';

import { logout } from 'redux/reducers/auth';

import useElementScroll from 'hooks/useElementScroll';

import { routes } from 'configs/navigation';

import ChatWidget, { DrawerHeader } from 'components/chat_widget';
import Header from 'components/Header';
import Breadcrumbs from 'components/Breadcrumbs';

import { GlobalSnackbarProvider } from 'hooks/useGlobalSnackbar';

import { RIGHT_SIDEBAR_WIDTH } from 'constants';
import { BreadcrumbProvider } from '../contexts/BreadcrumbContext';

export default function MainLayout() {
  const location = useLocation();

  const { i18n } = useTranslation();

  const currentRoute = useMemo(
    () =>
      routes.find(
        (route) =>
          route.path === location.pathname ||
          route.children?.find((child) =>
            location.pathname.includes(child.path.replace(/:(.*)/, ''))
          )
      ),
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
      <SEO />
      <GlobalSnackbarProvider>
        <BreadcrumbProvider>
          <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
            <NavAppBar position="fixed" open={open} elevation={0}>
              <Header />
            </NavAppBar>
            <Main ref={mainRef} open={open}>
              <DrawerHeader />
              <ContentContainer>
                <Breadcrumbs />
                <React.Suspense fallback={<LinearProgress sx={{ mb: 2 }} />}>
                  <TVTickerWidget isVisible={currentRoute?.displayTicker} />
                </React.Suspense>
                <PageContainer
                elevation={0}
                sx={{
                  bgcolor: 'background.paper',
                  borderRadius: { xs: 1, sm: 1.5 },
                  overflow: 'hidden',
                  minHeight: { xs: '50vh', lg: '80vh' },
                }}
              >
                <SwitchTransition>
                  <CSSTransition
                    unmountOnExit
                    key={location.pathname}
                    nodeRef={currentRoute?.ref || undefined}
                    timeout={300}
                    classNames="pages"
                  >
                    {() => <Outlet />}
                  </CSSTransition>
                </SwitchTransition>
              </PageContainer>
            </ContentContainer>
          </Main>
          {/* Scroll to top button */}
          <Zoom in={y > 300}>
            <ScrollToTopButton
              onClick={() => scrollTo({ top: 0, behavior: 'smooth' })}
              size="medium"
            >
              <KeyboardArrowUpIcon fontSize="medium" />
            </ScrollToTopButton>
          </Zoom>
            <ChatWidget
              isVisible={currentRoute?.displayChat}
              onStateChange={(state) => setOpen(state.open)}
            />
          </Box>
        </BreadcrumbProvider>
      </GlobalSnackbarProvider>
    </>
  );
}

// Floating animation for scroll-to-top button
const floatAnimation = keyframes`
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-4px);
  }
`;

// Modern main content area with smooth transitions and mesh gradient
const Main = styled(Box, { shouldForwardProp: (prop) => prop !== 'open' })(
  ({ theme, open }) => ({
    flexGrow: 1,
    paddingTop: theme.spacing(2),
    paddingBottom: theme.spacing(3),
    paddingLeft: theme.spacing(0.5),
    paddingRight: theme.spacing(0.5),
    [theme.breakpoints.up('sm')]: {
      paddingLeft: theme.spacing(1),
      paddingRight: theme.spacing(1),
    },
    [theme.breakpoints.up('md')]: {
      paddingLeft: theme.spacing(2),
      paddingRight: theme.spacing(2),
    },
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
    overflowX: 'hidden',
    position: 'relative',
    scrollBehavior: 'smooth',
    // Subtle mesh gradient background for depth
    '&::before': {
      content: '""',
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      height: '40vh',
      background: theme.palette.mode === 'dark'
        ? 'radial-gradient(ellipse 80% 50% at 50% -20%, rgba(0, 124, 255, 0.08), transparent)'
        : 'radial-gradient(ellipse 80% 50% at 50% -20%, rgba(0, 124, 255, 0.04), transparent)',
      pointerEvents: 'none',
      zIndex: -1,
    },
    // Custom scrollbar styling
    '&::-webkit-scrollbar': {
      width: 8,
      height: 8,
    },
    '&::-webkit-scrollbar-track': {
      background: theme.palette.background.default,
    },
    '&::-webkit-scrollbar-thumb': {
      background: theme.palette.grey[400],
      borderRadius: 4,
      '&:hover': {
        background: theme.palette.grey[500],
      },
    },
  })
);

// Modern app bar with glassmorphism effect
const NavAppBar = styled(AppBar, {
  shouldForwardProp: (prop) => prop !== 'open',
})(({ theme, open }) => ({
  backgroundImage: 'none',
  transition: theme.transitions.create(['margin', 'width', 'box-shadow'], {
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

// Content container with max width
const ContentContainer = styled(Box)(({ theme }) => ({
  maxWidth: theme.breakpoints.values.xxl,
  margin: '0 auto',
  width: '100%',
}));

// Page container with modern styling and subtle inner glow
const PageContainer = styled(Paper)(({ theme }) => ({
  display: 'flex',
  flex: 1,
  position: 'relative',
  boxShadow: theme.shadows[1],
  transition: theme.transitions.create(['box-shadow', 'border-color'], {
    duration: theme.transitions.duration.short,
  }),
  // Subtle border for depth
  border: `1px solid ${alpha(theme.palette.divider, 0.08)}`,
  // Inner highlight for glassmorphism effect
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '1px',
    background: theme.palette.mode === 'dark'
      ? 'linear-gradient(90deg, transparent 5%, rgba(255,255,255,0.06) 50%, transparent 95%)'
      : 'linear-gradient(90deg, transparent 5%, rgba(255,255,255,0.6) 50%, transparent 95%)',
    borderRadius: `${theme.shape.borderRadius}px ${theme.shape.borderRadius}px 0 0`,
    pointerEvents: 'none',
  },
  '&:hover': {
    boxShadow: theme.shadows[2],
    borderColor: alpha(theme.palette.primary.main, 0.08),
  },
}));

// Modern scroll to top button with floating animation and gradient
const ScrollToTopButton = styled(IconButton)(({ theme }) => ({
  position: 'fixed',
  bottom: theme.spacing(3),
  right: theme.spacing(3),
  background: theme.palette.gradients?.primary || theme.palette.primary.main,
  color: theme.palette.primary.contrastText,
  boxShadow: theme.palette.glows?.primary || theme.shadows[4],
  animation: `${floatAnimation} 3s ease-in-out infinite`,
  // Subtle inner glow
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    borderRadius: '50%',
    background: 'linear-gradient(180deg, rgba(255,255,255,0.15) 0%, transparent 50%)',
    pointerEvents: 'none',
  },
  '&:hover': {
    background: theme.palette.gradients?.primary || theme.palette.primary.dark,
    transform: 'scale(1.1)',
    boxShadow: theme.palette.glows?.primaryStrong || theme.shadows[6],
    animationPlayState: 'paused',
  },
  '&:active': {
    transform: 'scale(0.95)',
  },
  transition: theme.transitions.create(['background', 'transform', 'box-shadow'], {
    duration: theme.transitions.duration.short,
  }),
  [theme.breakpoints.down('sm')]: {
    bottom: theme.spacing(2),
    right: theme.spacing(2),
  },
}));

const TVTickerWidget = React.lazy(() =>
  import('components/trading_view/TVTickerWidget')
);