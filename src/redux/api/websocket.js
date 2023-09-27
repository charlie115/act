import { createApi } from '@reduxjs/toolkit/query/react';

import isEqual from 'lodash/isEqual';
import memoize from 'lodash/memoize';
import uniq from 'lodash/uniq';

import { storeAssetsList } from 'redux/reducers/websocket';

const websocketApi = createApi({
  reducerPath: 'websocketApi',
  endpoints: (build) => ({
    getWsCoins: build.query({
      queryFn: () => ({ data: {} }),
      onCacheEntryAdded: async (
        arg,
        {
          cacheDataLoaded,
          cacheEntryRemoved,
          dispatch,
          getState,
          updateCachedData,
        }
      ) => {
        const url = new URL(`${process.env.REACT_APP_DRF_WS_URL}/coins/`);
        url.searchParams.set('exchange_market_1', arg.baseMarket);
        url.searchParams.set('exchange_market_2', arg.targetMarket);
        url.searchParams.set('period', arg.period);
        const socket = new WebSocket(url.toString());

        const onMessage = memoize((event) => {
          const message = JSON.parse(event.data);
          try {
            const result = JSON.parse(message.result);
            updateCachedData((draft) => {
              result.forEach((item) => {
                if (!(item.base_asset in draft)) draft[item.base_asset] = {};
                if (!isEqual(item, draft[item.base_asset]))
                  draft[item.base_asset] = item;
              });
            });
            if (arg.isTableData) {
              const assets = uniq(result.map((asset) => asset.base_asset));
              const state = getState();
              if (!isEqual(assets, state.websocket.assets))
                dispatch(storeAssetsList(assets));
            }
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
    getRealTimeKline: build.query({
      queryFn: () => ({ data: {} }),
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
        const url = new URL(`${process.env.REACT_APP_DRF_WS_URL}/kline/`);
        url.searchParams.set('target_market_code', args.targetMarketCode);
        url.searchParams.set('origin_market_code', args.originMarketCode);
        url.searchParams.set('interval', args.interval);
        const socket = new WebSocket(url.toString());

        const onMessage = memoize((event) => {
          const message = JSON.parse(event.data);
          try {
            const result = JSON.parse(message.result);
            updateCachedData((draft) => {
              result.forEach((item) => {
                if (!(item.base_asset in draft)) draft[item.base_asset] = {};
                if (!isEqual(item, draft[item.base_asset]))
                  draft[item.base_asset] = item;
              });
            });
            if (args.isTableData) {
              const assets = uniq(result.map((asset) => asset.base_asset));
              const state = getState();
              if (!isEqual(assets, state.websocket.assets))
                dispatch(storeAssetsList(assets));
            }
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
export const { useGetWsCoinsQuery, useGetRealTimeKlineQuery } = websocketApi;
