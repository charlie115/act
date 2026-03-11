"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "./AuthProvider";

export default function AuthActions() {
  const router = useRouter();
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
      <Link className="auth-chip" href="/my-page">
        {user?.username || user?.email || "Account"}
      </Link>
      <button
        className="ghost-button ghost-button--button"
        onClick={async () => {
          await signOut();
          router.push("/");
        }}
        type="button"
      >
        Logout
      </button>
    </div>
  );
}
