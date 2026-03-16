"use client";

import { useEffect, useRef } from "react";

export default function TelegramConnectButton({ botUsername, onAuth }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!botUsername || !containerRef.current) return;

    const script = document.createElement("script");
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.setAttribute("data-telegram-login", botUsername);
    script.setAttribute("data-size", "large");
    script.setAttribute("data-radius", "8");
    script.setAttribute("data-request-access", "write");
    script.async = true;

    window.onTelegramAuth = (user) => {
      if (onAuth) onAuth(user);
    };
    script.setAttribute("data-onauth", "onTelegramAuth(user)");

    containerRef.current.innerHTML = "";
    containerRef.current.appendChild(script);

    return () => {
      delete window.onTelegramAuth;
    };
  }, [botUsername, onAuth]);

  return <div ref={containerRef} />;
}
