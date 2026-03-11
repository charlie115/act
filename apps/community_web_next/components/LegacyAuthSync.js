"use client";

import { useEffect } from "react";
import { useDispatch } from "react-redux";

import { useAuth } from "./auth/AuthProvider";
import { hydrateAuth } from "redux/reducers/auth";

export default function LegacyAuthSync() {
  const dispatch = useDispatch();
  const { loggedIn, tokens, user } = useAuth();

  useEffect(() => {
    const telegramBot =
      user?.socialapps?.find?.((item) => item.provider === "telegram")?.client_id || null;

    dispatch(
      hydrateAuth({
        id: tokens
          ? {
              accessToken: tokens.accessToken,
              refreshToken: tokens.refreshToken,
            }
          : null,
        loggedin: loggedIn,
        telegramBot,
        user: user || null,
      })
    );
  }, [dispatch, loggedIn, tokens, user]);

  return null;
}
