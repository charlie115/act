"use client";

import { useEffect, useId, useState } from "react";

import { useAuth } from "./AuthProvider";

export default function TelegramConnectButton() {
  const buttonId = useId().replace(/:/g, "");
  const { authorizedRequest, refreshUser, user } = useAuth();
  const [isPreparing, setIsPreparing] = useState(false);
  const [pageError, setPageError] = useState("");

  const telegramBot = user?.socialapps?.find((item) => item.provider === "telegram");

  useEffect(() => {
    if (!telegramBot?.client_id || !user?.uuid || user?.telegram_chat_id) {
      return undefined;
    }

    const container = document.getElementById(buttonId);
    if (!container) {
      return undefined;
    }

    container.innerHTML = "";

    window.TelegramWidget = {
      dataOnAuth: async (telegramUser) => {
        try {
          const response = await fetch("/api/auth/login/telegram/", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              user: user.uuid,
              ...telegramUser,
            }),
          });

          if (!response.ok) {
            throw new Error("Failed to connect Telegram.");
          }

          await refreshUser();
        } catch (requestError) {
          setPageError(requestError.message || "Failed to connect Telegram.");
        }
      },
    };

    const script = document.createElement("script");
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.async = true;
    script.setAttribute("data-telegram-login", telegramBot.client_id);
    script.setAttribute("data-size", "medium");
    script.setAttribute("data-request-access", "write");
    script.setAttribute("data-onauth", "TelegramWidget.dataOnAuth(user)");
    container.appendChild(script);

    return () => {
      delete window.TelegramWidget;
      container.innerHTML = "";
    };
  }, [buttonId, refreshUser, telegramBot?.client_id, user?.telegram_chat_id, user?.uuid]);

  async function handleAllocateBot() {
    setIsPreparing(true);
    setPageError("");

    try {
      await authorizedRequest("/auth/user/", {
        method: "PATCH",
        body: {
          telegram_bot: true,
        },
      });
      await refreshUser();
    } catch (requestError) {
      setPageError(requestError.payload?.detail || requestError.message || "Failed to allocate Telegram bot.");
    } finally {
      setIsPreparing(false);
    }
  }

  return (
    <div className="auth-form">
      {!telegramBot?.client_id ? (
        <button
          className="primary-button ghost-button--button auth-button"
          disabled={isPreparing}
          onClick={handleAllocateBot}
          type="button"
        >
          {isPreparing ? "Preparing..." : "Prepare Telegram Bot"}
        </button>
      ) : (
        <div id={buttonId} />
      )}
      {pageError ? <p className="auth-card__error">{pageError}</p> : null}
    </div>
  );
}
