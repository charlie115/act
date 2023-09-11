import React, { createRef } from 'react';

import {
  createBrowserRouter,
  createRoutesFromElements,
  Route,
} from 'react-router-dom';

import FullScreenLoading from 'components/FullScreenLoading';

import navigation from 'configs/navigation';

import { MainLayout, ProtectedLayout, PublicLayout } from './layouts';

const Arbitrage = React.lazy(() => import('pages/Arbitrage'));
const Home = React.lazy(() => import('pages/Home'));
const Login = React.lazy(() => import('pages/Login'));

export default createBrowserRouter(
  createRoutesFromElements(
    <Route element={<MainLayout />}>
      <Route element={<PublicLayout />}>
        {navigation.main.map(({ element: Element, ...props }) => (
          <Route
            key={props.name}
            element={
              <React.Suspense fallback={<FullScreenLoading />}>
                <Element />
              </React.Suspense>
            }
            {...props}
          />
        ))}
        {navigation.publicRoutes.map(({ element: Element, ...props }) => (
          <Route
            key={props.name}
            element={
              <React.Suspense fallback={<FullScreenLoading />}>
                <Element />
              </React.Suspense>
            }
            {...props}
          />
        ))}
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
