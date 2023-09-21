import React, { useEffect, useState } from 'react';

import { useLocation, useNavigate } from 'react-router-dom';

import AppBar from '@mui/material/AppBar';
import Avatar from '@mui/material/Avatar';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Container from '@mui/material/Container';
import IconButton from '@mui/material/IconButton';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Stack from '@mui/material/Stack';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';

import MenuIcon from '@mui/icons-material/Menu';

import { styled } from '@mui/material/styles';

import BrandLogo from 'components/BrandLogo';
import HeaderUserMenu from 'components/HeaderUserMenu';
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

  const [menuAnchorEl, setMenuAnchorEl] = useState(null);
  const [pages, setPages] = useState({});

  useEffect(() => {
    import('configs/navigation').then((res) => setPages(res.default));
  }, []);

  return (
    <AppBar position="sticky" sx={{ bgcolor: 'dark.light' }}>
      <Container maxWidth="xl">
        <Toolbar disableGutters>
          <BrandLogo
            onClick={() => navigate('/')}
            iconProps={{ color: 'white' }}
            sx={{ display: { xs: 'none', md: 'flex' } }}
          />
          <Box
            sx={{
              alignItems: 'center',
              flexGrow: 1,
              display: { xs: 'flex', md: 'none' },
            }}
          >
            <IconButton
              size="large"
              aria-label="header-menu"
              aria-controls="header-menu"
              aria-haspopup="true"
              onClick={(e) => setMenuAnchorEl(e.currentTarget)}
              color="white"
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
                <MenuItem
                  key={page.name}
                  onClick={() => navigate(page.path)}
                  selected={page.path === location.pathname}
                >
                  <Typography textAlign="center">{page.getTitle()}</Typography>
                </MenuItem>
              ))}
            </Menu>
            <BrandLogo
              onClick={() => navigate('/')}
              iconProps={{ color: 'white' }}
              sx={{ display: { xs: 'flex', md: 'none' } }}
            />
          </Box>
          <Box sx={{ flexGrow: 1, ml: 3, display: { xs: 'none', md: 'flex' } }}>
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
          <Stack
            direction="row"
            spacing={2}
            sx={{ display: { xs: 'none', sm: 'flex' } }}
          >
            <LanguageSelector />
            <ThemeSelector />
            <HeaderUserMenu />
            {/* <IconButton onClick={handleUserClick} sx={{ p: 0 }}>
              <Avatar
                src={user?.profile?.picture}
                alt={`${user?.first_name} ${user?.last_name}`}
                sx={{ bgcolor: user ? 'primary.main' : null }}
              />
            </IconButton> */}
          </Stack>

          <HeaderUserMenu
            iconStyle={{ display: { xs: 'block', sm: 'none' } }}
          />
          {/* <IconButton
            onClick={handleUserClick}
            sx={{ display: { xs: 'block', sm: 'none' }, p: 0 }}
          >
            <Avatar
              src={user?.profile?.picture}
              alt={`${user?.first_name} ${user?.last_name}`}
              sx={{ bgcolor: user ? 'primary.main' : null }}
            />
          </IconButton> */}
        </Toolbar>
      </Container>
    </AppBar>
  );
}
