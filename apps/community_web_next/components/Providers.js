"use client";

import { GoogleOAuthProvider } from "@react-oauth/google";

import AuthProvider from "./auth/AuthProvider";

const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

export default function Providers({ children }) {
  const content = <AuthProvider>{children}</AuthProvider>;

  if (!googleClientId) {
    return content;
  }

  return (
    <GoogleOAuthProvider clientId={googleClientId}>{content}</GoogleOAuthProvider>
  );
}
