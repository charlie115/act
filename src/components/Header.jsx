import React, { useEffect, useRef, useState } from 'react';

import { useLocation, useNavigate } from 'react-router-dom';

import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Container from '@mui/material/Container';
import IconButton from '@mui/material/IconButton';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';

import MenuIcon from '@mui/icons-material/Menu';

import routes from 'configs/router/routes';

export default function Header() {
  const location = useLocation();
  const navigate = useNavigate();

  const [menuAnchorEl, setMenuAnchorEl] = useState(null);
  const [userAnchorEl, setUserAnchorEl] = useState(null);

  return (
    <AppBar position="sticky">
      <Container maxWidth="xl">
        <Toolbar disableGutters>
          {/* <CommitIcon sx={{ display: { xs: 'none', md: 'flex' }, mr: 1 }} /> */}
          <Typography
            noWrap
            variant="h6"
            component="a"
            href="/"
            sx={{
              mr: 2,
              color: 'inherit',
              display: { xs: 'none', md: 'flex' },
              fontWeight: 700,
              letterSpacing: '.3rem',
              textDecoration: 'none',
            }}
          >
            AR-Kimp
          </Typography>

          <Box sx={{ flexGrow: 1, display: { xs: 'flex', md: 'none' } }}>
            <IconButton
              size="large"
              aria-label="menu-appbar"
              aria-controls="menu-appbar"
              aria-haspopup="true"
              onClick={(e) => setMenuAnchorEl(e.currentTarget)}
              color="inherit"
            >
              <MenuIcon />
            </IconButton>
            <Menu
              id="menu-appbar"
              anchorEl={menuAnchorEl}
              anchorOrigin={{
                vertical: 'bottom',
                horizontal: 'left',
              }}
              keepMounted
              transformOrigin={{ vertical: 'top', horizontal: 'left' }}
              open={!!menuAnchorEl}
              onClose={() => setMenuAnchorEl(null)}
              sx={{ display: { xs: 'block', md: 'none' } }}
            >
              {routes.pages.map((page) => (
                <MenuItem key={page.name} onClick={() => navigate(page.path)}>
                  <Typography textAlign="center">{page.title}</Typography>
                </MenuItem>
              ))}
            </Menu>
          </Box>

          {/* <CommitIcon sx={{ display: { xs: 'flex', md: 'none' }, mr: 1 }} /> */}
          <Typography
            noWrap
            variant="h6"
            component="a"
            href="/"
            sx={{
              mr: 2,
              color: 'inherit',
              display: { xs: 'flex', md: 'none' },
              fontWeight: 700,
              letterSpacing: '.3rem',
              textDecoration: 'none',
            }}
          >
            AR-Kimp
          </Typography>

          <Box sx={{ flexGrow: 1, display: { xs: 'none', md: 'flex' } }}>
            {routes.pages.map((page) => (
              <Button
                key={page.name}
                variant={page.path === location.pathname ? 'contained' : 'text'}
                onClick={() => navigate(page.path)}
                sx={{
                  my: 2,
                  color: 'inherit',
                  display: 'block',
                  fontSize: '0.9rem',
                  fontWeight: 700,
                }}
              >
                {page.title}
              </Button>
            ))}
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
}
