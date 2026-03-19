"use client";

import { GoogleOAuthProvider } from "@react-oauth/google";
import { Toaster } from "sonner";

import AuthProvider from "./auth/AuthProvider";

const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

export default function Providers({ children }) {
  const content = (
    <>
      <AuthProvider>{children}</AuthProvider>
      <Toaster
        theme="dark"
        position="bottom-right"
        toastOptions={{
          style: {
            background: "#121a2c",
            border: "1px solid rgba(115, 136, 181, 0.2)",
            color: "#eef2ff",
            fontSize: "0.84rem",
          },
        }}
      />
    </>
  );

  if (!googleClientId) {
    return content;
  }

  return (
    <GoogleOAuthProvider clientId={googleClientId}>{content}</GoogleOAuthProvider>
  );
}
