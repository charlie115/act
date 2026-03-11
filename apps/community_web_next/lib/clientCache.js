const cacheStore = new Map();

export async function fetchCachedJson(url, { ttlMs = 30000 } = {}) {
  const now = Date.now();
  const cached = cacheStore.get(url);

  if (cached && cached.expiresAt > now) {
    return cached.promise || cached.data;
  }

  const promise = fetch(url, { cache: "no-store" }).then(async (response) => {
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

  try {
    return await promise;
  } catch (error) {
    cacheStore.delete(url);
    throw error;
  }
}
