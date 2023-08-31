import React from 'react';

import {
  createBrowserRouter,
  createRoutesFromElements,
  Route,
} from 'react-router-dom';

import FullScreenLoading from 'components/FullScreenLoading';

import { MainLayout, ProtectedLayout, PublicLayout } from './layouts';

const Home = React.lazy(() => import('pages/Home'));
const Login = React.lazy(() => import('pages/Login'));

export default createBrowserRouter(
  createRoutesFromElements(
    <Route element={<MainLayout />}>
      <Route element={<PublicLayout />}>
        <Route
          index
          element={
            <React.Suspense fallback={<FullScreenLoading />}>
              <Home />
            </React.Suspense>
          }
        />
        <Route
          path="login"
          element={
            <React.Suspense fallback={<FullScreenLoading />}>
              <Login />
            </React.Suspense>
          }
        />

        <Route path="arbitrage" element={<div>Arbitrage</div>} />
        <Route path="investment" element={<div>Investment</div>} />
        <Route path="news" element={<div>News</div>} />
      </Route>
      <Route element={<ProtectedLayout />}>
        <Route
          index
          element={
            <React.Suspense fallback={<FullScreenLoading />}>
              <div>PrivatePage</div>
            </React.Suspense>
          }
        />
      </Route>
      {/* <Route path="*" element={<Navigate to="/" replace />} /> */}
      {/* <Route path="*" element={<PageNotFound />} /> */}
    </Route>
  )
);
