"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { MemoryRouter, useLocation, useNavigationType } from "react-router-dom";

import Header from "components/Header";

function HeaderRouteSync() {
  const location = useLocation();
  const navigationType = useNavigationType();
  const router = useRouter();

  useEffect(() => {
    const target = `${location.pathname}${location.search || ""}`;
    const current = `${window.location.pathname}${window.location.search}`;

    if (target === current) {
      return;
    }

    if (navigationType === "REPLACE") {
      router.replace(target);
      return;
    }

    router.push(target);
  }, [location, navigationType, router]);

  return null;
}

export default function LegacyHeaderShell() {
  const pathname = usePathname();

  return (
    <MemoryRouter key={pathname} initialEntries={[pathname]}>
      <HeaderRouteSync />
      <Header />
    </MemoryRouter>
  );
}
