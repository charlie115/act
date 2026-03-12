"use client";

import { useGoogleLogin } from "@react-oauth/google";

import { useAuth } from "./AuthProvider";

const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

function ActiveGoogleSignInButton() {
  const { isLoading, signInWithGoogle } = useAuth();

  const googleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      await signInWithGoogle(tokenResponse.access_token);
    },
  });

  if (!googleClientId) {
    return (
      <button className="primary-button auth-button" disabled type="button">
        Google OAuth 설정이 필요합니다
      </button>
    );
  }

  return (
    <button
      className="primary-button auth-button"
      disabled={isLoading}
      onClick={() => googleLogin()}
      type="button"
    >
      {isLoading ? "로그인 중..." : "Google로 로그인"}
    </button>
  );
}

export default function GoogleSignInButton() {
  if (!googleClientId) {
    return (
      <button className="primary-button auth-button" disabled type="button">
        Google OAuth 설정이 필요합니다
      </button>
    );
  }

  return <ActiveGoogleSignInButton />;
}
