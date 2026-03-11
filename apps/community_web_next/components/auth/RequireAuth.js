"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";

import { useAuth } from "./AuthProvider";

export default function RequireAuth({ children }) {
  const pathname = usePathname();
  const router = useRouter();
  const { isReady, loggedIn } = useAuth();

  useEffect(() => {
    if (isReady && !loggedIn) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
  }, [isReady, loggedIn, pathname, router]);

  if (!isReady || !loggedIn) {
    return (
      <section className="surface-card placeholder-card">
        <p className="eyebrow">Authentication</p>
        <h1>세션을 확인하는 중입니다.</h1>
        <p>로그인이 필요하면 로그인 페이지로 이동합니다.</p>
      </section>
    );
  }

  return children;
}
