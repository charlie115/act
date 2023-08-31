import { createApi } from '@reduxjs/toolkit/query/react';
import { current } from '@reduxjs/toolkit';

import { DateTime } from 'luxon';

import debounce from 'lodash/debounce';
import isEqual from 'lodash/isEqual';
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

const websocketApi = createApi({
  reducerPath: 'websocketApi',
  endpoints: (build) => ({
    getKpWebsocketData: build.query({
      queryFn: () => ({
        data: {
          coinList: [],
          coinData: {},
          coinPriceData: {},
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
                if (!draft.coinList.includes(name)) {
                  draft.coinList.push(name);
                  draft.coinData[name] = {
                    name,
                    id: name,
                    price: item.tp_kimp,
                    volume: item.acc_trade_price_24h,
                  };
                }
                draft.coinList.sort();

                if (!draft.coinPriceData[name])
                  draft.coinPriceData[name] = [
                    {
                      name,
                      id: name,
                      time: item.upbit_timestamp,
                      ...item,
                    },
                  ];

                // draft.coinData[name] = {
                //   name,
                //   id: name,
                //   price: item.tp_kimp,
                //   volume: item.acc_trade_price_24h,
                // };

                // draft.coinPriceData[name].push({
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
                    draft.coinData[name] = {
                      name,
                      id: name,
                      price: item.tp_kimp,
                      volume: item.acc_trade_price_24h,
                    };
                    draft.coinPriceData[name].push({
                      name,
                      id: name,
                      time: item.upbit_timestamp,
                      ...item,
                    });
                  }
                }
                if (draft.coinPriceData[name]?.length > CACHE_MAX_ENTRY)
                  draft.coinPriceData[name].shift();
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
export const { useGetDummyWebsocketDataQuery, useGetKpWebsocketDataQuery } =
  websocketApi;
