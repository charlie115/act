import React from 'react';

import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { useSelector } from 'react-redux';

import Box from '@mui/material/Box';
import Container from '@mui/material/Container';

import Header from 'components/Header';

export function ProtectedLayout() {
  const token = useSelector((state) => state.auth.token);

  const location = useLocation();

  if (!token)
    return <Navigate to="/signin" replace state={{ from: location }} />;

  return <Outlet />;
}

export function PublicLayout() {
  const token = useSelector((state) => state.auth.token);

  const location = useLocation();

  if (token) return <Navigate to="/" replace state={{ from: location }} />;

  return <Outlet />;
}

export function MainLayout() {
  return (
    <Box>
      <Header />
      <Container>
        <Outlet />
      </Container>
    </Box>
  );
}
