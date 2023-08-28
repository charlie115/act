import React from 'react';

import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { useSelector } from 'react-redux';

import Box from '@mui/material/Box';

import Header from 'components/Header';

const TVTickerWidget = React.lazy(() =>
  import('components/trading_view/TVTickerWidget')
);

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
      <Box sx={{ mb: 4, p: 1 }}>
        <Box
        // sx={{ position: 'sticky', top: 70 }}
        >
          <React.Suspense fallback={<Box />}>
            <TVTickerWidget />
          </React.Suspense>
        </Box>
        <Box sx={{ mt: 2 }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
}
