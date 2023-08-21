import { createApi } from '@reduxjs/toolkit/query/react';
import { current } from '@reduxjs/toolkit';
import coins from '../../.dummy/coins.json';

// TODO: Replace with actual URL
const ws = new WebSocket('ws://localhost:5001');
const connected = new Promise((resolve) => {
  if (ws) {
    ws.onopen = () => {
      // TODO: Temporary for dummy ws connection
      // ws.send('connected');
      resolve();
    };
  }
});

const handler = async (onMessage, { cacheDataLoaded, cacheEntryRemoved }) => {
  try {
    // wait for the initial query to resolve before proceeding
    await cacheDataLoaded;

    ws.addEventListener('message', onMessage);
  } catch {
    // no-op in case `cacheEntryRemoved` resolves before `cacheDataLoaded`,
    // in which case `cacheDataLoaded` will throw
  }
  // cacheEntryRemoved will resolve when the cache subscription is no longer active
  await cacheEntryRemoved;
  // perform cleanup steps once the `cacheEntryRemoved` promise resolves
  ws.close();
};

const websocketApi = createApi({
  baseQuery: async () => {
    await connected;
    return { data: {} };
  },
  endpoints: (build) => ({
    getCoins: build.query({
      queryFn: () => ({ data: { coins } }),
      onCacheEntryAdded: async (
        arg,
        { updateCachedData, cacheDataLoaded, cacheEntryRemoved }
      ) => {
        const onMessage = (event) => {
          // const data = JSON.parse(event.data);
          updateCachedData((draft) => {
            // TODO: Update message 'type'
            if (event.data.type !== 'get-coins') return;
            // TODO: Get coin list from actual data
            draft.coins = event.data.coins;
          });
        };

        await handler(onMessage, {
          cacheDataLoaded,
          cacheEntryRemoved,
        });
      },
    }),
  }),
});

export default websocketApi;
export const { useGetCoinsQuery } = websocketApi;
