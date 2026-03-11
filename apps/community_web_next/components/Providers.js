"use client";

import { CssBaseline, ThemeProvider } from "@mui/material";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { PersistGate } from "redux-persist/integration/react";
import { Provider as ReduxProvider } from "react-redux";
import { I18nextProvider } from "react-i18next";

import i18n from "configs/i18n";
import theme from "configs/theme";
import { persistor, store } from "redux/store";
import AuthProvider from "./auth/AuthProvider";
import LegacyAuthSync from "./LegacyAuthSync";

const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

export default function Providers({ children }) {
  const content = (
    <ReduxProvider store={store}>
      <PersistGate loading={null} persistor={persistor}>
        <I18nextProvider i18n={i18n}>
          <ThemeProvider theme={theme}>
            <CssBaseline />
            <AuthProvider>
              <LegacyAuthSync />
              {children}
            </AuthProvider>
          </ThemeProvider>
        </I18nextProvider>
      </PersistGate>
    </ReduxProvider>
  );

  if (!googleClientId) {
    return content;
  }

  return (
    <GoogleOAuthProvider clientId={googleClientId}>{content}</GoogleOAuthProvider>
  );
}
