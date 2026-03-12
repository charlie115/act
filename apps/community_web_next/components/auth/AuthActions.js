"use client";

import Link from "next/link";

import { useAuth } from "./AuthProvider";
import NextDepositBalance from "../header/NextDepositBalance";
import NextHeaderUserMenu from "../header/NextHeaderUserMenu";

export default function AuthActions() {
  const { isReady, loggedIn, user, signOut } = useAuth();

  if (!isReady) {
    return <span className="auth-chip">Checking session</span>;
  }

  if (!loggedIn) {
    return (
      <Link className="ghost-button" href="/login">
        Login
      </Link>
    );
  }

  return (
    <div className="auth-actions">
      <NextDepositBalance />
      <Link className="auth-chip" href="/my-page">
        {user?.username || user?.email || "Account"}
      </Link>
      <NextHeaderUserMenu />
    </div>
  );
}
