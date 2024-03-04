from django_filters import filterset

from lib.filters import CharArrayFilter, UserUuidFilter
from users.models import UserFavoriteAssets, UserProfile, DepositHistory


class UserFavoriteAssetsFilter(UserUuidFilter):
    market_codes = CharArrayFilter(field_name="market_codes", lookup_expr="contains")

    class Meta:
        model = UserFavoriteAssets
        fields = ("user", "base_asset", "market_codes")


class UserProfileFilter(UserUuidFilter):
    class Meta:
        model = UserProfile
        fields = ("user", "referral", "level", "points")


class DepositHistoryFilter(filterset.FilterSet):
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
