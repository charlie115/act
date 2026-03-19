"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import AuthCard from "../../components/auth/AuthCard";
import GoogleSignInButton from "../../components/auth/GoogleSignInButton";
import { useAuth } from "../../components/auth/AuthProvider";

export default function LoginClientPage({ nextPath = "/" }) {
  const router = useRouter();
  const { clearError, error, isReady, isVisitor, loggedIn } = useAuth();

  useEffect(() => {
    clearError();
  }, [clearError]);

  useEffect(() => {
    if (!isReady) {
      return;
    }

    if (isVisitor) {
      router.replace("/register");
      return;
    }

    if (loggedIn) {
      router.replace(nextPath);
    }
  }, [isReady, isVisitor, loggedIn, nextPath, router]);

  return (
    <AuthCard
      description="Google 계정으로 간편하게 로그인하세요."
      eyebrow="로그인"
      error={error}
      title="ArbiCrypto 로그인"
    >
      <GoogleSignInButton />
      <p className="auth-card__hint">
        신규 방문자는 로그인 후 자동으로 회원가입 단계로 이동합니다.
      </p>
      <Link className="inline-flex justify-center text-sm text-ink-muted hover:text-ink transition-colors" href="/">
        홈으로 돌아가기
      </Link>
    </AuthCard>
  );
}
