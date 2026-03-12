"use client";

import { CssBaseline, ThemeProvider } from "@mui/material";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { LocalizationProvider } from "@mui/x-date-pickers";
import { AdapterLuxon } from "@mui/x-date-pickers/AdapterLuxon";
import { PersistGate } from "redux-persist/integration/react";
import { Provider as ReduxProvider } from "react-redux";
import { I18nextProvider } from "react-i18next";

import i18n from "configs/i18n";
import { persistor, store } from "redux/store";
import { GlobalSnackbarProvider } from "hooks/useGlobalSnackbar";
import theme from "../legacy/configs/theme";
import AuthProvider from "./auth/AuthProvider";
import LegacyAuthSync from "./LegacyAuthSync";

const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

export default function Providers({ children }) {
  const content = (
    <ReduxProvider store={store}>
      <PersistGate loading={null} persistor={persistor}>
        <I18nextProvider i18n={i18n}>
          <LocalizationProvider dateAdapter={AdapterLuxon}>
            <ThemeProvider theme={theme}>
              <CssBaseline />
              <GlobalSnackbarProvider>
                <AuthProvider>
                  <LegacyAuthSync />
                  {children}
                </AuthProvider>
              </GlobalSnackbarProvider>
            </ThemeProvider>
          </LocalizationProvider>
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
