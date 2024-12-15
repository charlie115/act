SPECTACULAR_SETTINGS = {
    "TITLE": "Arbitrage Community APIs",
    "DESCRIPTION": "List of all available APIs in Arbitrage Community",
    "VERSION": "1.0.0",
    # 'AUTHENTICATION_WHITELIST': [
    #     'rest_framework_simplejwt.authentication.JWTAuthentication',
    #     'rest_framework.authentication.SessionAuthentication'
    # ],
    "SERVE_PERMISSIONS": ["lib.permissions.IsInternalOrAdmin"],
    "SERVE_INCLUDE_SCHEMA": False,
    "SORT_OPERATION_PARAMETERS": False,
    "EXTENSIONS_ROOT": {
        "x-tagGroups": [
            {
                "name": "AUTHENTICATION AND AUTHORIZATION",
                "tags": ["Auth"],
            },
            {
                "name": "BOARD",
                "tags": ["Post", "Comment", "PostLikes", "PostViews"],
            },
            {
                "name": "CHAT",
                "tags": ["PastChatMessages", "RandomUsername"],
            },
            {
                "name": "REFERRAL",
                "tags": [
                    "Referral",
                    "ReferralCode",
                    "ReferralCommission",
                    "Affiliate",
                    "SubAffiliate",
                    "AffiliateTier",
                    "AffiliateRequest",
                    "CommissionHistory",
                    "CommissionBalance",
                ],
            },
            {
                "name": "USER",
                "tags": [
                    "User",
                    "UserProfile",
                    "UserBlocklist",
                    "UserFavoriteAssets",
                    "DepositBalance",
                    "DepositHistory",
                    "WithdrawalRequest",
                ],
            },
            {
                "name": "WALLET",
                "tags": [
                    "UserWalletAddress",
                    "UserWalletBalance",
                    "UserWalletDeposit",
                ],
            },
            {
                "name": "COUPON",
                "tags": [
                    "Coupon",
                    "CouponRedemption",
                ],
            },
            {
                "name": "TRADE CORE",
                "tags": [
                    "Node",
                    "TradeConfig",
                    "Trade",
                    "ExchangeAPIKey",
                    "Capital",
                    "SpotPosition",
                    "FuturesPosition",
                    "OrderHistory",
                    "TradeHistory",
                    "PNLHistory",
                    "Pboundary",
                    "DepositAddress",
                    "DepositAmount",
                ],
            },
            {
                "name": "INFO CORE",
                "tags": [
                    "Asset",
                    "Dollar",
                    "FundingRate",
                    "Kline",
                    "MarketCodes",
                    "WalletStatus",
                ],
            },
            {
                "name": "MESSAGE CORE",
                "tags": ["Message"],
            },
            {
                "name": "NEWS CORE",
                "tags": ["Announcements", "News", "SNS Posts"],
            },
        ],
    },
}
