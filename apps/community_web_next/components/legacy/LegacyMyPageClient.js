"use client";

import MyPage from "pages/MyPage";
import LegacyRouterShell from "./LegacyRouterShell";

export default function LegacyMyPageClient() {
  return (
    <div className="legacy-surface legacy-surface--mypage">
      <LegacyRouterShell initialPath="/my-page">
        <MyPage />
      </LegacyRouterShell>
    </div>
  );
}
