"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { MemoryRouter, Routes, Route, useLocation, useNavigationType } from "react-router-dom";

function LegacyRouteSync({ mapPath }) {
  const location = useLocation();
  const navigationType = useNavigationType();
  const router = useRouter();

  useEffect(() => {
    const rawPath = `${location.pathname}${location.search || ""}`;
    const target = mapPath ? mapPath(rawPath, location) : rawPath;
    const current = `${window.location.pathname}${window.location.search}`;

    if (!target || target === current) {
      return;
    }

    if (navigationType === "REPLACE") {
      router.replace(target);
      return;
    }

    router.push(target);
  }, [location, mapPath, navigationType, router]);

  return null;
}

export default function LegacyRouterShell({ children, initialPath = "/", mapPath }) {
  return (
    <MemoryRouter initialEntries={[initialPath]}>
      <LegacyRouteSync mapPath={mapPath} />
      <Routes>
        <Route index element={children} path="*" />
      </Routes>
    </MemoryRouter>
  );
}
