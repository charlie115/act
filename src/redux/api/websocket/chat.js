import memoize from 'lodash/memoize';

import { DateTime } from 'luxon';

import websocketApi from 'redux/api/websocket';
import {
  websocketConnected,
  websocketDisconnected,
} from 'redux/reducers/websocket';

const url = new URL(`${process.env.REACT_APP_DRF_WS_URL}/chat/`);
const socket = new WebSocket(url.toString());

const connected = new Promise((resolve) => {
  resolve();
});

const api = websocketApi.injectEndpoints({
  endpoints: (build) => ({
    getMessages: build.query({
      queryFn: () => ({ data: { message: null } }),
      onCacheEntryAdded: async (
        args,
        { dispatch, cacheDataLoaded, cacheEntryRemoved, updateCachedData }
      ) => {
        await connected;

        const onOpen = () => dispatch(websocketConnected('chat'));
        const onClose = () => dispatch(websocketDisconnected('chat'));

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
          socket.addEventListener('open', onOpen);
          socket.addEventListener('close', onClose);
        } catch {
          // no-op in case `cacheEntryRemoved` resolves before `cacheDataLoaded`,
          // in which case `cacheDataLoaded` will throw
        }
        await cacheEntryRemoved;

        socket.removeEventListener('message', onMessage);
        socket.removeEventListener('open', onOpen);
        socket.removeEventListener('close', onClose);
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
