import memoize from 'lodash/memoize';

import { DateTime } from 'luxon';

import websocketApi from 'redux/api/websocket';
import {
  websocketConnected,
  websocketDisconnected,
} from 'redux/reducers/websocket';

const url = new URL(
  `${process.env.REACT_APP_DRF_WS_URL}${
    process.env.REACT_APP_ENV !== 'production' ? '' : '/api'
  }/chat/`
);
let ws;

const getConnection = async () => {
  if (!ws || ws.readyState === WebSocket.CLOSED)
    ws = new WebSocket(url.toString());
  return ws;
};

const api = websocketApi.injectEndpoints({
  endpoints: (build) => ({
    getMessages: build.query({
      keepUnusedDataFor: 300,
      queryFn: () => ({ data: { message: null } }),
      onCacheEntryAdded: async (
        args,
        { dispatch, cacheDataLoaded, cacheEntryRemoved, updateCachedData }
      ) => {
        const socket = await getConnection();

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

        socket.close();
        socket.removeEventListener('message', onMessage);
        socket.removeEventListener('open', onOpen);
        setTimeout(() => {
          socket.removeEventListener('close', onClose);
        }, 35000);
      },
    }),
    sendMessage: build.mutation({
      queryFn: async ({ username, message, email }) => {
        const socket = await getConnection();
        socket.send(JSON.stringify({ username, message, email }));
        return { username, message, email };
      },
    }),
  }),
});

export default api;
export const { useGetMessagesQuery, useSendMessageMutation } = api;
