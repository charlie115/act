import { createApi } from '@reduxjs/toolkit/query/react';
import { createEntityAdapter, current } from '@reduxjs/toolkit';

// TODO: Refactor when all websocket connections are finalized
let dummyWs;
const getDummyWebsocketConnection = async () => {
  if (!dummyWs) dummyWs = new WebSocket('ws://localhost:5001');
  return dummyWs;
};

let kpWs;
const getKpWebsocketConnection = async () => {
  if (!kpWs || kpWs.readyState !== WebSocket.OPEN)
    kpWs = new WebSocket('ws://221.148.128.213:22180/ws/kp_websocket/v1');

  return kpWs;
};

export const coinsAdapter = createEntityAdapter({
  selectId: (coin) => coin.symbol,
});

const websocketApi = createApi({
  reducerPath: 'websocketApi',
  endpoints: (build) => ({
    getDummyWebsocketData: build.query({
      keepUnusedDataFor: 60,
      queryFn: () => ({ data: { chart: [], coins: [] } }),
      onCacheEntryAdded: async (
        arg,
        { cacheDataLoaded, cacheEntryRemoved, getCacheEntry, updateCachedData }
      ) => {
        const socket = await getDummyWebsocketConnection();
        const onMessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            updateCachedData((draft) => {
              // TODO: Update message 'type'
              // TODO: Get data from actual data
              switch (message.type) {
                case 'chart':
                  draft.chart = message.data;
                  break;
                case 'coins':
                  draft.coins = message.data;
                  break;
                default:
                  break;
              }
            });
          } catch {
            /* ignore */
          }
        };
        try {
          await cacheDataLoaded;
          socket.addEventListener('message', onMessage);
        } catch {
          // no-op in case `cacheEntryRemoved` resolves before `cacheDataLoaded`,
          // in which case `cacheDataLoaded` will throw
        }
        await cacheEntryRemoved;
        socket.close();
      },
    }),
    getKpWebsocketData: build.query({
      queryFn: () => ({
        data: { coins: coinsAdapter.getInitialState() },
        // data: { allMessages: [], coinList: [], coinListPrev: [] },
      }),
      // serializeQueryArgs: ({ queryArgs }) => Object.keys(queryArgs).join(),
      // transformResponse: (response) =>
      //   coinsAdapter.addMany(coinsAdapter.getInitialState(), response),
      onCacheEntryAdded: async (
        arg,
        { cacheDataLoaded, cacheEntryRemoved, getCacheEntry, updateCachedData }
      ) => {
        const MAX_ENTRY = 100;
        const socket = await getKpWebsocketConnection();

        const onMessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            updateCachedData((draft) => {
              switch (message.type) {
                case 'push':
                  {
                    const result = JSON.parse(message.result);
                    coinsAdapter.upsertMany(draft.coins, result);
                    // console.log('coinsAdapter: ', coinsAdapter);
                    // draft.allMessages.push(result);
                    // const coinListPrev =
                    //   draft.allMessages[draft.allMessages.length - 2]?.map(
                    //     (coin) => ({
                    //       ...coin,
                    //       id: coin.symbol,
                    //       name: coin.symbol.endsWith('USDT')
                    //         ? coin.symbol.slice(0, -4)
                    //         : coin.symbol,
                    //       price: coin.tp_kimp,
                    //       volume: coin.acc_trade_price_24h,
                    //     })
                    //   ) || [];
                    // const coinList = result.map((coin) => ({
                    //   ...coin,
                    //   id: coin.symbol,
                    //   name: coin.symbol.endsWith('USDT')
                    //     ? coin.symbol.slice(0, -4)
                    //     : coin.symbol,
                    //   price: coin.tp_kimp,
                    //   volume: coin.acc_trade_price_24h,
                    // }));
                    // draft.coinList = coinList;
                    // draft.coinListPrev = coinListPrev;
                  }
                  break;
                default:
                  break;
              }
            });
          } catch (e) {
            console.log('e: ', e);
            /* ignore */
          }
        };
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
  }),
});

export default websocketApi;
export const { useGetDummyWebsocketDataQuery, useGetKpWebsocketDataQuery } =
  websocketApi;

export const { selectAll } = coinsAdapter.getSelectors((state) => state.coins);
