"use client";

import { useEffect, useMemo, useState } from "react";

import { fetchCachedJson } from "../../../lib/clientCache";

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
    let socket = null;

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

        setLiveRows(Array.isArray(payload) ? payload : []);
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

    const connect = () => {
      socket = new WebSocket(url.toString());

      socket.addEventListener("open", () => {
        setConnected(true);
        setError("");
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
            const next = Array.isArray(current) ? [...current] : [];
            const nextIndex = new Map(next.map((item, index) => [item.base_asset, index]));

            payload.forEach((item) => {
              if (!item?.base_asset) {
                return;
              }

              const existingIndex = nextIndex.get(item.base_asset);
              if (existingIndex === undefined) {
                nextIndex.set(item.base_asset, next.length);
                next.push(item);
              } else {
                next[existingIndex] = item;
              }
            });

            return next;
          });

          setLastReceivedAt(Date.now());
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
        if (!active) {
          return;
        }
        reconnectTimer = window.setTimeout(connect, 1500);
      });
    };

    seedCurrentSnapshot();
    connect();

    return () => {
      active = false;
      if (reconnectTimer) {
        window.clearTimeout(reconnectTimer);
      }
      if (socket) {
        socket.close();
      }
    };
  }, [originMarketCode, targetMarketCode]);

  const sortedRows = useMemo(
    () =>
      [...liveRows].sort(
        (left, right) => Number(right.atp24h || 0) - Number(left.atp24h || 0)
      ),
    [liveRows]
  );

  return { liveRows: sortedRows, connected, error, lastReceivedAt };
}
