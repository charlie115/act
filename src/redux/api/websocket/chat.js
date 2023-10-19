import memoize from 'lodash/memoize';

import { DateTime } from 'luxon';

import websocketApi from 'redux/api/websocket';

// const url = new URL('ws://172.30.1.34:8000/chat/');
const url = new URL(`${process.env.REACT_APP_DRF_WS_URL}/chat/`);
const socket = new WebSocket(url.toString());

const connected = new Promise((resolve) => {
  socket.onopen = () => {
    resolve();
  };
});

socket.onclose = () => {
  console.log('disconnected');
};

const api = websocketApi.injectEndpoints({
  endpoints: (build) => ({
    getMessages: build.query({
      queryFn: () => ({ data: { message: null } }),
      // queryFn: () => ({ data: { messages: [] } }),
      onCacheEntryAdded: async (
        args,
        { cacheDataLoaded, cacheEntryRemoved, updateCachedData }
      ) => {
        await connected;
        const onMessage = memoize((event) => {
          const message = JSON.parse(event.data);
          try {
            updateCachedData((currentCacheData) => {
              currentCacheData.message = {
                ...message,
                id: DateTime.now().toMillis(),
              };
            });
          } catch {
            /* empty */
          }
        });

        try {
          await cacheDataLoaded;
          socket.addEventListener('message', onMessage);
        } catch {
          // no-op in case `cacheEntryRemoved` resolves before `cacheDataLoaded`,
          // in which case `cacheDataLoaded` will throw
        }
        await cacheEntryRemoved;

        socket.removeEventListener('message', onMessage);
        socket.close();
      },
    }),
    sendMessage: build.mutation({
      queryFn: async ({ username, message, email }) => {
        await connected;
        socket.send(JSON.stringify({ username, message, email }));
        return { username, message, email };
      },
    }),
  }),
});

export default api;
export const { useGetMessagesQuery, useSendMessageMutation } = api;
