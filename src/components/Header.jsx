import React, { useEffect, useMemo, useState } from 'react';

import { useLocation, useNavigate } from 'react-router-dom';

import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Stack from '@mui/material/Stack';
import Toolbar from '@mui/material/Toolbar';

import MenuIcon from '@mui/icons-material/Menu';

import { styled } from '@mui/material/styles';

import { useSelector } from 'react-redux';

import BrandLogo from 'components/BrandLogo';
import HeaderUserMenu from 'components/HeaderUserMenu';
import DepositBalance from 'components/DepositBalance';
import LanguageSelector from 'components/LanguageSelector';
import ThemeSelector from 'components/ThemeSelector';

const MenuButton = styled(Button, {
  shouldForwardProp: (prop) => prop !== 'active',
})(({ active, theme }) => ({
  color: active ? theme.palette.primary.main : 'white',
  display: 'block',
  fontSize: '0.9em',
  fontWeight: 700,
  minWidth: 'unset',
  textDecoration: active ? 'underline' : 'none',
  textUnderlineOffset: 8,
}));

export default function Header() {
  const location = useLocation();
  const navigate = useNavigate();

  const { loggedin } = useSelector((state) => state.auth);

  const [menuAnchorEl, setMenuAnchorEl] = useState(null);
  const [pages, setPages] = useState();

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

  useEffect(() => {
    // location.pathname
  }, [location.pathname]);

  return (
    // <AppBar position="sticky" sx={{ bgcolor: 'dark.light' }}>
    //   <Container maxWidth="xxl">
    <Toolbar sx={{ maxHeight: 65.6 }}>
      <Box
        sx={{
          alignItems: 'center',
          display: { xs: 'flex', md: 'none' },
          mr: 1,
        }}
      >
        <IconButton
          aria-label="header-menu"
          aria-controls="header-menu"
          aria-haspopup="true"
          color="white"
          size="large"
          onClick={(e) => setMenuAnchorEl(e.currentTarget)}
          sx={{ p: 0 }}
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
          {pages?.map((page) => (
            <MenuItem
              key={page.name}
              onClick={() => {
                navigate(page.path);
                setMenuAnchorEl(null);
              }}
              selected={page.path === currentRoute?.path}
            >
              <ListItemIcon>
                <page.icon />
              </ListItemIcon>
              <ListItemText sx={{ fontWeight: 700 }}>
                {page?.getTitle()}
              </ListItemText>
            </MenuItem>
          ))}
        </Menu>
      </Box>
      <BrandLogo
        onClick={() => navigate('/')}
        sx={{ flexGrow: { xs: 1, md: 0 } }}
      />
      <Box sx={{ flexGrow: 1, ml: 3, display: { xs: 'none', md: 'flex' } }}>
        {pages?.map((page) => (
          <MenuButton
            key={page.name}
            active={page.path === currentRoute?.path}
            onClick={() => navigate(page.path)}
            sx={{ fontSize: { md: 11, lg: '1em' }, ml: 1, my: 2, px: 1 }}
          >
            {page?.getTitle()}
          </MenuButton>
        ))}
      </Box>
      <Stack
        useFlexGap
        flexWrap="wrap"
        direction="row"
        spacing={{ xs: 1, sm: 2 }}
        sx={{ alignItems: 'center', justifyContent: 'end' }}
      >
        {loggedin && <DepositBalance />}
        <LanguageSelector />
        <ThemeSelector />
        <HeaderUserMenu />
      </Stack>
    </Toolbar>
    //   </Container>
    // </AppBar>
  );
}
