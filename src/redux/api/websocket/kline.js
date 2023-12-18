import isEqual from 'lodash/isEqual';
import memoize from 'lodash/memoize';

import { DateTime } from 'luxon';

import websocketApi from 'redux/api/websocket';

import { DATE_FORMAT_API_QUERY } from 'constants';

const api = websocketApi.injectEndpoints({
  endpoints: (build) => ({
    getRealTimeKline: build.query({
      keepUnusedDataFor: 1,
      queryFn: () => ({ data: {} }),
      onCacheEntryAdded: async (
        args,
        { cacheDataLoaded, cacheEntryRemoved, updateCachedData }
      ) => {
        const url = new URL(
          `${process.env.REACT_APP_DRF_WS_URL}${
            process.env.REACT_APP_ENV !== 'production' ? '' : '/api'
          }/kline/`
        );
        url.searchParams.set('target_market_code', args.targetMarketCode);
        url.searchParams.set('origin_market_code', args.originMarketCode);
        url.searchParams.set('interval', args.interval);
        const socket = new WebSocket(url.toString());

        const onMessage = memoize((event) => {
          const message = JSON.parse(event.data);
          try {
            if (message.type === 'connect') return;

            const result = JSON.parse(message.result);
            updateCachedData((draft) => {
              result.forEach((item) => {
                const dateTimeString = DateTime.fromMillis(
                  item.datetime_now
                ).toFormat(DATE_FORMAT_API_QUERY);
                item.datetime_now = DateTime.fromISO(dateTimeString).toMillis();

                if (!(item.base_asset in draft)) draft[item.base_asset] = {};
                if (!isEqual(item, draft[item.base_asset]))
                  draft[item.base_asset] = item;
              });
            });
          } catch {
            /* empty */
          }
        });

        const onClose = memoize(() => {
          console.log('here');
          try {
            updateCachedData((draft) => {
              draft.status = 'DISCONNECTED';
            });
          } catch {
            /* empty */
          }
        });
        try {
          await cacheDataLoaded;
          socket.addEventListener('message', onMessage);
          socket.addEventListener('close', onClose);
        } catch {
          // no-op in case `cacheEntryRemoved` resolves before `cacheDataLoaded`,
          // in which case `cacheDataLoaded` will throw
        }
        await cacheEntryRemoved;

        socket.close();
        socket.removeEventListener('message', onMessage);
      },
    }),
  }),
});

export default api;
export const { useGetRealTimeKlineQuery } = api;
