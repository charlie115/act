import { createApi } from '@reduxjs/toolkit/query/react';

import isEqual from 'lodash/isEqual';
import memoize from 'lodash/memoize';
import uniq from 'lodash/uniq';

import { DateTime } from 'luxon';

import websocketApi from 'redux/api/websocket';

const api = websocketApi.injectEndpoints({
  endpoints: (build) => ({
    getChatMessages: build.query({
      queryFn: () => ({ data: { messages: [] } }),
      onCacheEntryAdded: async (
        args,
        {
          cacheDataLoaded,
          cacheEntryRemoved,
          dispatch,
          getState,
          updateCachedData,
        }
      ) => {
        const url = new URL(`${process.env.REACT_APP_DRF_WS_URL}/chat/`);
        const socket = new WebSocket(url.toString());

        const onMessage = memoize((event) => {
          const message = JSON.parse(event.data);
          try {
            console.log(message);
          } catch {
            /* empty */
          }
        });

        try {
          await cacheDataLoaded;
          socket.addEventListener(
            'message',
            onMessage
            // throttle(onMessage, 1000, { leading: true })
          );
        } catch {
          // no-op in case `cacheEntryRemoved` resolves before `cacheDataLoaded`,
          // in which case `cacheDataLoaded` will throw
        }
        await cacheEntryRemoved;

        socket.removeEventListener('message', onMessage);
        socket.close();
      },
    }),
  }),
});

export default api;
export const { useGetChatMessagesQuery } = api;
