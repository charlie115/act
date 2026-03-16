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
        className="rounded-lg bg-accent px-4 py-2 text-sm font-bold text-white transition-colors hover:bg-accent/80"
      >
        로그인
      </Link>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <Link href="/my-page" className="text-sm text-ink-muted hover:text-ink transition-colors">
        {user?.email?.split("@")[0] || "마이페이지"}
      </Link>
      <button
        onClick={logout}
        className="rounded-lg border border-border px-3 py-1.5 text-xs text-ink-muted transition-colors hover:bg-surface-elevated hover:text-ink"
        type="button"
      >
        로그아웃
      </button>
    </div>
  );
}
