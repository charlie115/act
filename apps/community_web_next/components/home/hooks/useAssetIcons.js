"use client";

import { useEffect, useState } from "react";

import { fetchCachedJson } from "../../../lib/clientCache";

/**
 * Fetches asset icon URLs from the backend and returns a symbol → URL map.
 * Icons are cached for 10 minutes since they rarely change.
 */
export default function useAssetIcons() {
  const [iconMap, setIconMap] = useState({});

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const payload = await fetchCachedJson("/api/infocore/assets/", {
          ttlMs: 600_000,
        });
        const results = payload?.results || payload || [];

        if (!active) {
          return;
        }

        const map = {};

        for (const item of results) {
          if (item.symbol && item.icon) {
            map[item.symbol.toUpperCase()] = item.icon;
          }
        }

        setIconMap(map);
      } catch {
        // fall back to empty map — PremiumTable will hide broken icons
      }
    }

    load();

    return () => {
      active = false;
    };
  }, []);

  return iconMap;
}
