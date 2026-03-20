const MAX_ENTRIES = 300;
const cacheStore = new Map();

// Global API token for X-Api-Token header injection
let _apiToken = "";
export function setGlobalApiToken(token) { _apiToken = token; }
export function getGlobalApiToken() { return _apiToken; }

function evict() {
  // Prune expired entries first
  const now = Date.now();
  for (const [key, entry] of cacheStore) {
    if (entry.expiresAt <= now && !entry.promise) {
      cacheStore.delete(key);
    }
  }

  // If still over limit, drop oldest (LRU — Map iterates in insertion order)
  while (cacheStore.size > MAX_ENTRIES) {
    const oldestKey = cacheStore.keys().next().value;
    cacheStore.delete(oldestKey);
  }
}

function touch(key) {
  const entry = cacheStore.get(key);
  if (entry) {
    cacheStore.delete(key);
    cacheStore.set(key, entry);
  }
}

export async function fetchCachedJson(url, { ttlMs = 30000, fetchOptions = {} } = {}) {
  const now = Date.now();
  const cached = cacheStore.get(url);

  if (cached && cached.expiresAt > now) {
    touch(url);
    return cached.promise || cached.data;
  }

  const headers = { ...fetchOptions.headers };
  if (_apiToken) headers["X-Api-Token"] = _apiToken;

  const promise = fetch(url, { cache: "no-store", ...fetchOptions, headers }).then(async (response) => {
    if (!response.ok) {
      throw new Error(`Failed to fetch ${url}: ${response.status}`);
    }

    const data = await response.json();
    cacheStore.set(url, {
      data,
      expiresAt: Date.now() + ttlMs,
    });
    return data;
  });

  cacheStore.set(url, {
    promise,
    expiresAt: now + ttlMs,
  });

  evict();

  try {
    return await promise;
  } catch (error) {
    cacheStore.delete(url);
    throw error;
  }
}

// ── Kline history cache ──────────────────────────────────────────────
// Dedicated cache for kline chart data with stale-while-revalidate.
// Key: "target:origin:asset:interval" — not URL-based.
// Stores the full candle array with long TTLs since WebSocket handles live updates.

const KLINE_MAX_ENTRIES = 100;
const klineStore = new Map();

export function getKlineCache(key) {
  const entry = klineStore.get(key);
  if (!entry) return null;

  // LRU touch
  klineStore.delete(key);
  klineStore.set(key, entry);

  return {
    data: entry.data,
    fresh: Date.now() < entry.expiresAt,
  };
}

export function setKlineCache(key, data, ttlMs) {
  klineStore.set(key, {
    data,
    expiresAt: Date.now() + ttlMs,
  });

  // LRU eviction
  while (klineStore.size > KLINE_MAX_ENTRIES) {
    const oldest = klineStore.keys().next().value;
    klineStore.delete(oldest);
  }
}
