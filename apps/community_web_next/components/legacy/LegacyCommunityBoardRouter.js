"use client";

import { useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  MemoryRouter,
  Route,
  Routes,
  useLocation,
  useNavigationType,
} from "react-router-dom";

import CommunityBoard from "pages/community-board";
import CommunityBoardPost from "pages/community-board/CommunityBoardPost";
import CommunityBoardPostNew from "pages/community-board/CommunityBoardPostNew";

function buildNextPath(location) {
  const params = new URLSearchParams(location.search || "");
  let pathname = location.pathname;

  if (pathname === "/community-board" && location.state?.category && !params.has("category")) {
    params.set("category", location.state.category);
  }

  if (pathname === "/login" && location.state?.from?.pathname) {
    pathname = "/login";
    params.set("next", location.state.from.pathname);
  }

  const query = params.toString();
  return query ? `${pathname}?${query}` : pathname;
}

function LegacyBoardRouteSync() {
  const location = useLocation();
  const navigationType = useNavigationType();
  const router = useRouter();

  useEffect(() => {
    const target = buildNextPath(location);
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

export default function LegacyCommunityBoardRouter({
  initialCategory,
  initialPath = "/community-board",
}) {
  const initialEntries = useMemo(
    () => [
      {
        pathname: initialPath,
        state: initialCategory ? { category: initialCategory } : null,
      },
    ],
    [initialCategory, initialPath]
  );

  return (
    <div className="legacy-surface legacy-surface--board">
      <MemoryRouter initialEntries={initialEntries}>
        <LegacyBoardRouteSync />
        <Routes>
          <Route path="/community-board" element={<CommunityBoard />}>
            <Route path="post/new" element={<CommunityBoardPostNew />} />
            <Route path="post/:postId" element={<CommunityBoardPost />} />
          </Route>
        </Routes>
      </MemoryRouter>
    </div>
  );
}
