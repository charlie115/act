import { createApi } from '@reduxjs/toolkit/query/react';
import { current } from '@reduxjs/toolkit';

import { DateTime } from 'luxon';

import debounce from 'lodash/debounce';
import isEqual from 'lodash/isEqual';
import memoize from 'lodash/memoize';
import throttle from 'lodash/throttle';

import { storeCoins } from 'redux/reducers/websocket';

const CACHE_MAX_ENTRY = 1000;

// TODO: Refactor when all websocket connections are finalized
let kpWs;
const getKpWebsocketConnection = async () => {
  if (!kpWs || kpWs.readyState !== WebSocket.OPEN)
    kpWs = new WebSocket('ws://221.148.128.213:22180/ws/kp_websocket/v1');

  return kpWs;
};

const websocketBaseQuery = (url, token) => {};

const websocketApi = createApi({
  reducerPath: 'websocketApi',
  endpoints: (build) => ({
    getWsCoins: build.query({
      queryFn: () => ({
        data: {},
      }),
      // serializeQueryArgs: ({ queryArgs }) => Object.keys(queryArgs).join(),
      // transformResponse: (response) =>
      //   coinsAdapter.addMany(coinsAdapter.getInitialState(), response),
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
        url.searchParams.set('exchange_market_1', arg.baseMarket);
        url.searchParams.set('exchange_market_2', arg.compareMarket);
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
                // if (!(item.datetime_now in draft[item.base_asset]))
                //   draft[item.base_asset][item.datetime_now] = item;
                // else if (
                //   !isEqual(item, draft[item.base_asset][item.datetime_now])
                // )
                //   draft[item.base_asset][item.datetime_now] = item;
              });
            });
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
    getKpWebsocketData: build.query({
      queryFn: () => ({
        data: {
          coinList: [],
          coinRealTimeData: {},
          coinSeriesData: {},
          coinTimestamps: {},
        },
      }),
      // serializeQueryArgs: ({ queryArgs }) => Object.keys(queryArgs).join(),
      // transformResponse: (response) =>
      //   coinsAdapter.addMany(coinsAdapter.getInitialState(), response),
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
        const socket = await getKpWebsocketConnection();

        const onMessage = (event) => {
          const message = JSON.parse(event.data);
          if (message.type === 'connect') return;
          try {
            const result = JSON.parse(message.result);
            updateCachedData((draft) => {
              result.forEach((item) => {
                const name = item.symbol.endsWith('USDT')
                  ? item.symbol.slice(0, -4)
                  : item.symbol;
                if (!draft.coinList.includes(name)) draft.coinList.push(name);

                // draft.coinList.sort();
                draft.coinRealTimeData[name] = {
                  name,
                  id: name,
                  change: item.tp_kimp,
                  kimp: item.tp_kimp,
                  price: item.trade_price,
                  volume: item.acc_trade_price_24h,
                  ...item,
                };

                if (!draft.coinSeriesData[name])
                  draft.coinSeriesData[name] = [
                    {
                      name,
                      id: name,
                      time: item.upbit_timestamp,
                      ...item,
                    },
                  ];

                // draft.coinRealTimeData[name] = {
                //   name,
                //   id: name,
                //   price: item.tp_kimp,
                //   volume: item.acc_trade_price_24h,
                // };

                // draft.coinSeriesData[name].push({
                //   name,
                //   id: name,
                //   time: item.upbit_timestamp,
                //   ...item,
                // });

                if (draft.coinTimestamps[name]) {
                  const diff = DateTime.fromMillis(item.upbit_timestamp).diff(
                    DateTime.fromMillis(draft.coinTimestamps[name]),
                    ['milliseconds']
                  );
                  if (diff.values.milliseconds > 100) {
                    draft.coinSeriesData[name].push({
                      name,
                      id: name,
                      time: item.upbit_timestamp,
                      ...item,
                    });
                  }
                }
                if (draft.coinSeriesData[name]?.length > CACHE_MAX_ENTRY)
                  draft.coinSeriesData[name].shift();
                draft.coinTimestamps[name] = item.upbit_timestamp;
              });
            });

            const cache = getCacheEntry();
            const state = getState();
            if (!isEqual(cache.data.coinList, state.websocket.coins))
              dispatch(storeCoins(cache.data.coinList));
          } catch {
            /* empty */
          }
        };

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
export const { useGetWsCoinsQuery, useGetKpWebsocketDataQuery } = websocketApi;
