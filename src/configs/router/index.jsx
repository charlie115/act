import React from 'react';

import {
  createBrowserRouter,
  createRoutesFromElements,
  Route,
} from 'react-router-dom';

import FullScreenLoading from 'components/FullScreenLoading';

import navigation from 'configs/navigation';

import { MainLayout, ProtectedLayout, PublicLayout } from './layouts';

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
        {navigation.protectedRoutes.map(({ element: Element, ...props }) => (
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
      {/* <Route path="*" element={<Navigate to="/" replace />} /> */}
      {/* <Route path="*" element={<PageNotFound />} /> */}
    </Route>
  )
);
