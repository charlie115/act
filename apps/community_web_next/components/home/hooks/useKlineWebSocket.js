"use client";

import { useEffect, useState } from "react";

import { toast } from "sonner";
import { fetchCachedJson } from "../../../lib/clientCache";

const RECONNECT_BASE_MS = 1500;
const RECONNECT_MAX_MS = 30000;
const STALE_THRESHOLD_MS = 15000; // 15초간 메시지 없으면 stale

export default function useKlineWebSocket(targetMarketCode, originMarketCode) {
  const [liveRows, setLiveRows] = useState([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState("");
  const [lastReceivedAt, setLastReceivedAt] = useState(null);

  useEffect(() => {
    if (!targetMarketCode || !originMarketCode) {
      return;
    }

    let active = true;
    let reconnectTimer = null;
    let staleCheckTimer = null;
    let socket = null;
    let reconnectAttempt = 0;
    let lastMessageTime = 0;

    async function seedCurrentSnapshot() {
      try {
        const payload = await fetchCachedJson(
          `/api/infocore/kline-current/?target_market_code=${encodeURIComponent(
            targetMarketCode
          )}&origin_market_code=${encodeURIComponent(originMarketCode)}`,
          { ttlMs: 250 }
        );

        if (!active) {
          return;
        }

        setLiveRows((current) =>
          current.length > 0 ? current : (Array.isArray(payload) ? payload : [])
        );
      } catch {
        if (!active) {
          return;
        }
        setLiveRows([]);
      }
    }

    const wsBase = (
      process.env.NEXT_PUBLIC_DRF_WS_URL ||
      process.env.NEXT_PUBLIC_DRF_URL?.replace(/^http/i, "ws") ||
      window.location.origin.replace(/^http/i, "ws")
    ).replace(/\/$/, "");

    const url = new URL(`${wsBase}/kline/`);
    url.searchParams.set("target_market_code", targetMarketCode);
    url.searchParams.set("origin_market_code", originMarketCode);
    url.searchParams.set("interval", "1T");

    function scheduleReconnect() {
      if (!active) return;
      const delay = Math.min(RECONNECT_BASE_MS * Math.pow(2, reconnectAttempt), RECONNECT_MAX_MS);
      reconnectAttempt += 1;
      reconnectTimer = window.setTimeout(connect, delay);
    }

    function connect() {
      if (!active) return;
      if (socket) {
        socket.onclose = null;
        socket.close();
      }

      socket = new WebSocket(url.toString());

      socket.addEventListener("open", () => {
        setConnected(true);
        setError("");
        reconnectAttempt = 0;
        lastMessageTime = Date.now();
      });

      socket.addEventListener("message", (event) => {
        const message = JSON.parse(event.data);
        if (message.type !== "publish") {
          return;
        }

        try {
          const payload = JSON.parse(message.result);
          if (!Array.isArray(payload)) {
            return;
          }

          setLiveRows((current) => {
            if (!Array.isArray(current)) return payload;

            const currentIndex = new Map(current.map((item, i) => [item.base_asset, i]));
            let changed = false;
            let next = null;

            for (const item of payload) {
              if (!item?.base_asset) continue;
              const idx = currentIndex.get(item.base_asset);
              if (idx === undefined) {
                // New asset — must copy
                if (!next) next = [...current];
                next.push(item);
                changed = true;
              } else if (current[idx] !== item) {
                // Changed asset — lazy copy on first change
                if (!next) next = [...current];
                next[idx] = item;
                changed = true;
              }
            }

            return changed ? next : current;
          });

          const now = Date.now();
          lastMessageTime = now;
          setLastReceivedAt(now);
        } catch {
          // Ignore malformed websocket payloads.
        }
      });

      socket.addEventListener("error", () => {
        setConnected(false);
        setError("실시간 프리미엄 연결이 불안정합니다.");
      });

      socket.addEventListener("close", () => {
        setConnected(false);
        scheduleReconnect();
      });
    }

    // Stale connection check — if OPEN but no messages for 15s, force reconnect
    function checkStale() {
      if (!active) return;
      if (
        socket &&
        socket.readyState === WebSocket.OPEN &&
        lastMessageTime > 0 &&
        Date.now() - lastMessageTime > STALE_THRESHOLD_MS
      ) {
        setConnected(false);
        setError("데이터 수신 지연 — 재연결 중...");
        socket.close(); // triggers close → scheduleReconnect
      }
    }

    staleCheckTimer = window.setInterval(checkStale, 5000);

    // Visibility change — reconnect on tab focus return if disconnected or stale
    function handleVisibilityChange() {
      if (document.visibilityState !== "visible" || !active) return;

      // If socket is closed or closing, reconnect immediately
      if (!socket || socket.readyState === WebSocket.CLOSED || socket.readyState === WebSocket.CLOSING) {
        if (reconnectTimer) window.clearTimeout(reconnectTimer);
        reconnectAttempt = 0;
        connect();
        seedCurrentSnapshot();
        toast.info("실시간 데이터 재연결 중...");
        return;
      }

      // If socket is open but stale, force reconnect
      if (lastMessageTime > 0 && Date.now() - lastMessageTime > STALE_THRESHOLD_MS) {
        socket.close(); // triggers close → scheduleReconnect
        seedCurrentSnapshot();
      }
    }

    document.addEventListener("visibilitychange", handleVisibilityChange);

    seedCurrentSnapshot();
    connect();

    return () => {
      active = false;
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      if (reconnectTimer) window.clearTimeout(reconnectTimer);
      if (staleCheckTimer) window.clearInterval(staleCheckTimer);
      if (socket) {
        socket.onclose = null;
        socket.close();
      }
    };
  }, [originMarketCode, targetMarketCode]);

  return { liveRows, connected, error, lastReceivedAt };
}
