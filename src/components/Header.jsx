import React, { useCallback, useEffect, useState } from 'react';

import { useLocation, useNavigate } from 'react-router-dom';

import AppBar from '@mui/material/AppBar';
import Avatar from '@mui/material/Avatar';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Container from '@mui/material/Container';
import IconButton from '@mui/material/IconButton';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Slide from '@mui/material/Slide';
import Stack from '@mui/material/Stack';
import Switch from '@mui/material/Switch';
import SvgIcon from '@mui/material/SvgIcon';
import Toolbar from '@mui/material/Toolbar';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import MenuIcon from '@mui/icons-material/Menu';

import { styled } from '@mui/material/styles';

import debounce from 'lodash/debounce';

import { useDispatch, useSelector } from 'react-redux';
import { toggleTheme } from 'redux/reducers/app';

import { ReactComponent as SiBitcoin } from 'assets/svg/bitcoincash.svg';
import MoonSvg from 'assets/svg/moon.svg';
import SunSvg from 'assets/svg/sun.svg';

import LanguageSelector from 'components/LanguageSelector';

export default function Header() {
  const dispatch = useDispatch();
  const location = useLocation();
  const navigate = useNavigate();

  const currentTheme = useSelector((state) => state.app.theme);

  const [hidden, setHidden] = useState(false);
  const [menuAnchorEl, setMenuAnchorEl] = useState(null);
  const [pages, setPages] = useState({});
  // const [userAnchorEl, setUserAnchorEl] = useState(null);

  const showHeader = useCallback(
    debounce(() => setHidden(false), 500),
    []
  );

  const handleScroll = () => {
    if (window.scrollY > 300) {
      setHidden(true);
      showHeader();
    }
  };

  useEffect(() => {
    import('configs/navigation').then((res) => setPages(res.default));

    window.addEventListener('scroll', handleScroll);
    return () => window.addEventListener('scroll', handleScroll);
  }, []);

  return (
    <Slide in={!hidden}>
      <AppBar position="sticky" sx={{ bgcolor: 'dark.light' }}>
        <Container maxWidth="xl">
          <Toolbar disableGutters>
            <SvgIcon
              color="primary"
              fontSize="medium"
              sx={{ display: { xs: 'none', md: 'flex' }, mr: 1 }}
            >
              <SiBitcoin />
            </SvgIcon>
            <NavTitle
              noWrap
              variant="h6"
              component="a"
              href="/"
              sx={{ display: { xs: 'none', md: 'flex' } }}
            >
              AR-Kimp
            </NavTitle>
            {/* Small screen */}
            <Box sx={{ flexGrow: 1, display: { xs: 'flex', md: 'none' } }}>
              <IconButton
                size="large"
                aria-label="header-menu"
                aria-controls="header-menu"
                aria-haspopup="true"
                onClick={(e) => setMenuAnchorEl(e.currentTarget)}
                color="inherit"
              >
                <MenuIcon />
              </IconButton>
              <Menu
                id="header-menu"
                anchorEl={menuAnchorEl}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
                keepMounted
                transformOrigin={{ vertical: 'top', horizontal: 'left' }}
                open={!!menuAnchorEl}
                onClose={() => setMenuAnchorEl(null)}
                sx={{ display: { xs: 'block', md: 'none' } }}
              >
                {pages.main?.map((page) => (
                  <MenuItem key={page.name} onClick={() => navigate(page.path)}>
                    <Typography textAlign="center">
                      {page.getTitle()}
                    </Typography>
                  </MenuItem>
                ))}
              </Menu>
            </Box>
            <SvgIcon
              color="primary"
              size="medium"
              sx={{ display: { xs: 'flex', md: 'none' }, mr: 1 }}
            >
              <SiBitcoin />
            </SvgIcon>
            <NavTitle
              noWrap
              variant="h6"
              component="a"
              href="/"
              sx={{ display: { xs: 'flex', md: 'none' } }}
            >
              AR-Kimp
            </NavTitle>
            <Box
              sx={{ flexGrow: 1, ml: 3, display: { xs: 'none', md: 'flex' } }}
            >
              {pages.main?.map((page) => (
                <MenuButton
                  key={page.name}
                  active={page.path === location.pathname}
                  onClick={() => navigate(page.path)}
                  sx={{ ml: 1, my: 2, px: 1 }}
                >
                  {page.getTitle()}
                </MenuButton>
              ))}
            </Box>
            <Stack direction="row" spacing={2} sx={{ flexGrow: 0 }}>
              <LanguageSelector />
              <ThemeToggle
                checked={currentTheme === 'dark'}
                onChange={(e) =>
                  dispatch(toggleTheme(e.target.checked ? 'dark' : 'light'))
                }
              />
              <IconButton onClick={() => {}} sx={{ p: 0 }}>
                <Avatar />
              </IconButton>
            </Stack>
          </Toolbar>
        </Container>
      </AppBar>
    </Slide>
  );
}

const MenuButton = styled(Button, {
  shouldForwardProp: (prop) => prop !== 'active',
})(({ active, theme }) => ({
  color: active ? theme.palette.info.main : 'inherit',
  display: 'block',
  fontSize: '0.9rem',
  fontWeight: 700,
  minWidth: 'unset',
  textDecoration: active ? 'underline' : 'none',
  textUnderlineOffset: 8,
}));

const NavTitle = styled(Typography)(() => ({
  mr: 4,
  color: 'inherit',
  fontWeight: 700,
  letterSpacing: '.3rem',
  textDecoration: 'none',
}));

const ThemeToggle = styled(Switch)(({ theme }) => ({
  width: 62,
  height: 34,
  padding: 7,
  '& .MuiSwitch-switchBase': {
    margin: 1,
    padding: 0,
    transform: 'translateX(6px)',
    '&.Mui-checked': {
      color: '#fff',
      transform: 'translateX(22px)',
      '& .MuiSwitch-thumb:before': {
        backgroundImage: `url(${MoonSvg})`,
      },
      '& + .MuiSwitch-track': {
        opacity: 1,
        backgroundColor: theme.palette.secondary.main,
      },
    },
  },
  '& .MuiSwitch-thumb': {
    backgroundColor:
      theme.palette.mode === 'dark'
        ? theme.palette.dark.light
        : 'theme.palette.light.main',
    width: 32,
    height: 32,
    '&:before': {
      content: "''",
      position: 'absolute',
      width: '100%',
      height: '100%',
      left: 0,
      top: 0,
      backgroundRepeat: 'no-repeat',
      backgroundPosition: 'center',
      backgroundImage: `url(${SunSvg})`,
    },
  },
  '& .MuiSwitch-track': {
    opacity: 1,
    backgroundColor: theme.palette.secondary.main,
    borderRadius: 20 / 2,
  },
}));
