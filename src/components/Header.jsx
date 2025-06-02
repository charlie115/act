import React, { useEffect, useMemo, useState } from 'react';

import { useLocation, useNavigate } from 'react-router-dom';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Container from '@mui/material/Container';
import Drawer from '@mui/material/Drawer';
import IconButton from '@mui/material/IconButton';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Stack from '@mui/material/Stack';
import Toolbar from '@mui/material/Toolbar';
import useMediaQuery from '@mui/material/useMediaQuery';
import Fade from '@mui/material/Fade';
import Divider from '@mui/material/Divider';

import MenuIcon from '@mui/icons-material/Menu';
import CloseIcon from '@mui/icons-material/Close';

import { styled, useTheme, alpha } from '@mui/material/styles';

import { useSelector } from 'react-redux';

import BrandLogo from 'components/BrandLogo';
import HeaderUserMenu from 'components/HeaderUserMenu';
import DepositBalance from 'components/DepositBalance';

// Modern navigation button with hover effects
const NavButton = styled(Button, {
  shouldForwardProp: (prop) => prop !== 'active',
})(({ active, theme }) => ({
  color: active ? theme.palette.primary.main : theme.palette.text.primary,
  fontSize: '0.875rem',
  fontWeight: active ? 600 : 500,
  letterSpacing: '0.02em',
  minWidth: 'unset',
  padding: theme.spacing(1, 2),
  position: 'relative',
  textTransform: 'none',
  transition: theme.transitions.create(['color', 'background-color'], {
    duration: theme.transitions.duration.short,
  }),
  '&:hover': {
    backgroundColor: alpha(theme.palette.primary?.main || '#007cff', 0.08),
    color: theme.palette.primary.main,
  },
  '&::after': {
    content: '""',
    position: 'absolute',
    bottom: 0,
    left: '50%',
    transform: 'translateX(-50%)',
    width: active ? '80%' : '0%',
    height: 3,
    backgroundColor: theme.palette.primary.main,
    borderRadius: '3px 3px 0 0',
    transition: theme.transitions.create(['width'], {
      duration: theme.transitions.duration.short,
    }),
  },
  '&:hover::after': {
    width: '80%',
  },
}));

// Modern mobile drawer styling
const MobileDrawer = styled(Drawer)(({ theme }) => ({
  '& .MuiDrawer-paper': {
    width: 280,
    backgroundColor: theme.palette.background.paper,
    borderRight: `1px solid ${theme.palette.divider}`,
  },
}));

// Styled logo container with animation
const LogoContainer = styled(Box)(({ theme }) => ({
  cursor: 'pointer',
  transition: theme.transitions.create(['transform'], {
    duration: theme.transitions.duration.short,
  }),
  '&:hover': {
    transform: 'scale(1.05)',
  },
  '&:active': {
    transform: 'scale(0.98)',
  },
}));

// Mobile menu header
const DrawerHeader = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: theme.spacing(2),
  borderBottom: `1px solid ${theme.palette.divider}`,
}));

export default function Header() {
  const theme = useTheme();
  const location = useLocation();
  const navigate = useNavigate();

  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const { loggedin } = useSelector((state) => state.auth);

  const [mobileOpen, setMobileOpen] = useState(false);
  const [pages, setPages] = useState([]);
  const [scrolled, setScrolled] = useState(false);

  const currentRoute = useMemo(
    () =>
      pages?.find(
        (page) =>
          page.path === location.pathname ||
          page.children?.find((child) =>
            location.pathname.includes(child.path.replace(/:(.*)/, ''))
          )
      ),
    [pages, location.pathname]
  );

  useEffect(() => {
    import('configs/navigation').then((res) =>
      setPages(res.default?.main?.filter((page) => page.displayInHeader))
    );
  }, []);

  // Handle scroll effect for header
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Close mobile drawer on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleNavigate = (path) => {
    navigate(path);
    setMobileOpen(false);
  };

  // Mobile drawer content
  const drawer = (
    <>
      <DrawerHeader>
        <BrandLogo onClick={() => handleNavigate('/')} />
        <IconButton
          onClick={handleDrawerToggle}
          sx={{ color: theme.palette.text.secondary }}
        >
          <CloseIcon />
        </IconButton>
      </DrawerHeader>
      <List sx={{ px: 1, py: 2 }}>
        {pages?.map((page) => (
          <ListItem key={page.name} disablePadding sx={{ mb: 0.5 }}>
            <ListItemButton
              onClick={() => handleNavigate(page.path)}
              selected={page.path === currentRoute?.path}
              sx={{
                borderRadius: 1.5,
                py: 1.5,
                '&.Mui-selected': {
                  backgroundColor: alpha(theme.palette.primary?.main || '#007cff', 0.12),
                  color: theme.palette.primary.main,
                  '& .MuiListItemIcon-root': {
                    color: theme.palette.primary.main,
                  },
                },
                '&:hover': {
                  backgroundColor: alpha(theme.palette.primary?.main || '#007cff', 0.08),
                },
              }}
            >
              {page.icon && (
                <ListItemIcon sx={{ minWidth: 40 }}>
                  <page.icon />
                </ListItemIcon>
              )}
              <ListItemText 
                primary={page?.getTitle()} 
                primaryTypographyProps={{
                  fontSize: '0.875rem',
                  fontWeight: page.path === currentRoute?.path ? 600 : 500,
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      {loggedin && (
        <>
          <Divider sx={{ mx: 2 }} />
          <Box sx={{ p: 2 }}>
            <DepositBalance fullWidth />
          </Box>
        </>
      )}
    </>
  );

  return (
    <Toolbar
      sx={{
        minHeight: { xs: 64, sm: 70 },
        px: { xs: 2, sm: 3, md: 4 },
        py: 1,
        backgroundColor: scrolled 
          ? alpha(theme.palette.background?.paper || '#ffffff', 0.8)
          : theme.palette.background.paper,
        backdropFilter: scrolled ? 'blur(10px)' : 'none',
        borderBottom: `1px solid ${
          scrolled ? theme.palette.divider : 'transparent'
        }`,
        transition: theme.transitions.create(
          ['background-color', 'backdrop-filter', 'border-color'],
          {
            duration: theme.transitions.duration.short,
          }
        ),
      }}
    >
      <Container
        maxWidth="xxl"
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          px: { xs: 0, sm: 2 },
        }}
      >
        {/* Mobile menu button */}
        {isMobile && (
          <IconButton
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ 
              mr: 2,
              color: theme.palette.text.primary,
              '&:hover': {
                backgroundColor: alpha(theme.palette.primary?.main || '#007cff', 0.08),
              },
            }}
          >
            <MenuIcon />
          </IconButton>
        )}

        {/* Logo */}
        <LogoContainer>
          <BrandLogo
            onClick={() => navigate('/')}
            sx={{
              height: { xs: 32, sm: 36 },
              width: 'auto',
            }}
          />
        </LogoContainer>

        {/* Desktop navigation */}
        {!isMobile && (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 0.5,
              mx: 4,
              flex: 1,
            }}
          >
            {pages?.map((page) => (
              <Fade key={page.name} in timeout={300}>
                <NavButton
                  active={page.path === currentRoute?.path}
                  onClick={() => navigate(page.path)}
                >
                  {page?.getTitle()}
                </NavButton>
              </Fade>
            ))}
          </Box>
        )}

        {/* Right side actions */}
        <Stack
          direction="row"
          spacing={{ xs: 1, sm: 2 }}
          sx={{
            alignItems: 'center',
            ml: isMobile ? 'auto' : 0,
          }}
        >
          {loggedin && !isMobile && <DepositBalance />}
          <HeaderUserMenu />
        </Stack>

        {/* Mobile drawer */}
        <MobileDrawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile
          }}
        >
          {drawer}
        </MobileDrawer>
      </Container>
    </Toolbar>
  );
}