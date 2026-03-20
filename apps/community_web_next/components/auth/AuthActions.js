"use client";

import Link from "next/link";
import { useAuth } from "./AuthProvider";

export default function AuthActions() {
  const { loggedIn, user, logout, loading } = useAuth();

  if (loading) return null;

  if (!loggedIn) {
    return (
      <Link
        href="/login"
        className="w-full text-center block rounded-lg bg-gradient-to-r from-accent to-[#4da0ff] px-4 py-2 text-sm font-bold text-white shadow-[0_0_16px_-3px_rgba(43,115,255,0.4)] transition-all hover:shadow-[0_0_24px_-3px_rgba(43,115,255,0.6)] hover:brightness-110"
      >
        로그인
      </Link>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <Link href="/my-page" className="min-w-0 truncate text-sm text-ink-muted hover:text-ink transition-colors">
        {user?.email?.split("@")[0] || "마이페이지"}
      </Link>
      <button
        onClick={logout}
        className="flex-shrink-0 rounded-lg border border-border px-3 py-1.5 text-xs text-ink-muted transition-colors hover:bg-surface-elevated hover:text-ink"
        type="button"
      >
        로그아웃
      </button>
    </div>
  );
}
