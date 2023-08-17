import React from 'react';

import {
  createBrowserRouter,
  createRoutesFromElements,
  Route,
} from 'react-router-dom';

import FullLoading from 'components/FullLoading';

import { MainLayout, ProtectedLayout, PublicLayout } from './layouts';

const Home = React.lazy(() => import('pages/Home'));

export default createBrowserRouter(
  createRoutesFromElements(
    <Route element={<MainLayout />}>
      <Route element={<PublicLayout />}>
        <Route
          index
          element={
            <React.Suspense fallback={<FullLoading />}>
              <Home />
            </React.Suspense>
          }
        />
        <Route path="arbitrage" element={<div>Arbitrage</div>} />
      </Route>
      <Route element={<ProtectedLayout />}>
        <Route
          index
          element={
            <React.Suspense fallback={<FullLoading />}>
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
