"use client";

import { MemoryRouter, Outlet, Route, Routes } from "react-router-dom";

function OutletContextBridge({ context }) {
  return <Outlet context={context} />;
}

export default function LegacyOutletContextRouter({ children, context }) {
  return (
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route element={<OutletContextBridge context={context} />}>
          <Route index element={children} />
        </Route>
      </Routes>
    </MemoryRouter>
  );
}
