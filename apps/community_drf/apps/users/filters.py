from django_filters import filterset

from lib.filters import CharArrayFilter, UserUuidFilter
from users.models import UserFavoriteAssets, UserProfile, DepositBalance, DepositHistory


class UserFavoriteAssetsFilter(UserUuidFilter):
    market_codes = CharArrayFilter(field_name="market_codes", lookup_expr="contains")

    class Meta:
        model = UserFavoriteAssets
        fields = ("user", "base_asset", "market_codes")


class UserProfileFilter(UserUuidFilter):
    class Meta:
        model = UserProfile
        fields = ("user", "level", "points")


class DepositBalanceFilter(UserUuidFilter):
    class Meta:
        model = DepositBalance
        fields = [
            "user",
            "balance",
            "last_update",
        ]


class DepositHistoryFilter(UserUuidFilter):
    type = filterset.CharFilter(field_name="type")

    class Meta:
        model = DepositHistory
        fields = [
            "user",
            "balance",
            "change",
            "txid",
            "type",
            "pending",
            "registered_datetime",
        ]
