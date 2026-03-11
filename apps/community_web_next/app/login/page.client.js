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
      description="현재 DRF 인증 계약을 그대로 사용합니다. Google OAuth 완료 후 사용자 상태를 불러와 세션을 유지합니다."
      eyebrow="Authentication"
      error={error}
      title="ACW 계정 로그인"
    >
      <GoogleSignInButton />
      <p className="auth-card__hint">
        신규 방문자는 로그인 후 자동으로 회원가입 단계로 이동합니다.
      </p>
      <Link className="ghost-button auth-inline-button" href="/">
        홈으로 돌아가기
      </Link>
    </AuthCard>
  );
}
