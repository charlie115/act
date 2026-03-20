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
        richColors
        closeButton
        theme="dark"
        position="bottom-right"
        offset={72}
        duration={5000}
        toastOptions={{
          style: {
            background: "#121a2c",
            border: "1px solid rgba(115, 136, 181, 0.2)",
            color: "#eef2ff",
            fontSize: "0.84rem",
            borderRadius: "14px",
            boxShadow: "0 16px 40px rgba(0,0,0,0.4)",
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
