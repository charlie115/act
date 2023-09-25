import { createApi } from '@reduxjs/toolkit/query/react';
import { current } from '@reduxjs/toolkit';

import { DateTime } from 'luxon';

import debounce from 'lodash/debounce';
import isEqual from 'lodash/isEqual';
import memoize from 'lodash/memoize';
import uniq from 'lodash/uniq';

import { storeAssetsList } from 'redux/reducers/websocket';

const CACHE_MAX_ENTRY = 1000;

const websocketApi = createApi({
  reducerPath: 'websocketApi',
  endpoints: (build) => ({
    getWsCoins: build.query({
      queryFn: () => ({
        data: {},
      }),
      // serializeQueryArgs: ({ queryArgs }) => Object.keys(queryArgs).join(),
      // transformResponse: (response) =>
      onCacheEntryAdded: async (
        arg,
        {
          cacheDataLoaded,
          cacheEntryRemoved,
          dispatch,
          getCacheEntry,
          getState,
          updateCachedData,
        }
      ) => {
        const url = new URL(`${process.env.REACT_APP_DRF_WS_URL}/ws/coins/`);
        url.searchParams.set('exchange_market_1', arg.baseExchange);
        url.searchParams.set('exchange_market_2', arg.compareExchange);
        url.searchParams.set('period', arg.period);
        const socket = new WebSocket(url.toString());

        const onMessage = memoize((event) => {
          const message = JSON.parse(event.data);
          try {
            const result = JSON.parse(message.result);
            console.log('result: ', result);
            updateCachedData((draft) => {
              result.forEach((item) => {
                if (!(item.base_asset in draft)) draft[item.base_asset] = {};
                if (!isEqual(item, draft[item.base_asset]))
                  draft[item.base_asset] = item;
                // if (!(item.datetime_now in draft[item.base_asset]))
                //   draft[item.base_asset][item.datetime_now] = item;
                // else if (
                //   !isEqual(item, draft[item.base_asset][item.datetime_now])
                // )
                //   draft[item.base_asset][item.datetime_now] = item;
              });
            });
            const assets = uniq(result.map((asset) => asset.base_asset));
            const state = getState();
            if (!isEqual(assets, state.websocket.assets))
              dispatch(storeAssetsList(assets));
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

export default websocketApi;
export const { useGetWsCoinsQuery } = websocketApi;
