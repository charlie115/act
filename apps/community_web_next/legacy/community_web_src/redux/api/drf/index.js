import { createApi } from '@reduxjs/toolkit/query/react';

import baseQueryWithReAuth from 'utils/baseQueryWithReAuth';

const api = createApi({
  reducerPath: 'drfApi',
  baseQuery: baseQueryWithReAuth,
  tagTypes: [
    'AffiliateRequest',
    'AiRankRecommendation',
    'AllRepeatTrades',
    'AllTradeLogs',
    'AllTrades',
    'AllTriggerScanners',
    'Assets',
    'Capital',
    'CommunityBoardComments',
    'CommunityBoardPost',
    'CommunityBoardPostCategory',
    'CommunityBoardPosts',
    'CouponRedemption',
    'ExchangeApiKey',
    'FavoriteAssets',
    'FundingRateByMarketCode',
    'ReferralCode',
    'Refferal',
    'RepeatTradesByTradeConfig',
    'TelegramMessages',
    'TradeConfig',
    'TradesByTradeConfig',
    'TriggerScannersByTradeConfig',
    'User',
    'VolatilityNotifications',
    'WalletTransaction',
    'WithdrawalRequests',
  ],
  endpoints: () => ({}),
  refetchOnFocus: false,
  refetchOnMountOrArgChange: false,
  refetchOnReconnect: false,
});

export default api;
