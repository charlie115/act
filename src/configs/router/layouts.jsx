import React from 'react';

import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { useSelector } from 'react-redux';

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
