from django.core.validators import MinValueValidator, MaxValueValidator
from drf_spectacular.utils import extend_schema_field, inline_serializer
from rest_framework import serializers

from infocore.mixins import AssetMixin
from infocore.models import Asset, VolatilityNotificationConfig
from lib.datetime import DATE_TIME_FORMAT, DATE_TIME_TZ_FORMAT, UTC, TZ_UTC
from lib.fields import (
    CharacterSeparatedField,
    DateTimeWithTzField,
    FloatOrNoneField,
    TimezoneField,
)


class AssetSerializer(AssetMixin, serializers.ModelSerializer):
    def create(self, validated_data):
        asset_info = self.pull_asset_info(validated_data["symbol"])

        validated_data["icon"] = self.get_icon_image(asset_info)

        if "note" in asset_info:
            validated_data["note"] = asset_info["note"]

        return super().create(validated_data)

    class Meta:
        model = Asset
        fields = ("id", "symbol", "icon")
        extra_kwargs = {
            "icon": {"read_only": True},
        }


class KlineDataQueryParamsSerializer(serializers.Serializer):
    target_market_code = serializers.CharField(required=True)
    origin_market_code = serializers.CharField(required=True)
    base_asset = serializers.CharField(required=True)
    interval = serializers.CharField(required=True)
    start_time = serializers.DateTimeField(
        required=False,
        input_formats=[DATE_TIME_FORMAT],
    )
    end_time = serializers.DateTimeField(
        required=False,
        input_formats=[DATE_TIME_FORMAT],
    )
    tz = TimezoneField(default=UTC)


class KlineDataSerializer(serializers.Serializer):
    base_asset = serializers.CharField()
    datetime_now = DateTimeWithTzField(
        format=DATE_TIME_TZ_FORMAT,
        default_timezone=TZ_UTC,
    )
    tp_open = FloatOrNoneField()
    tp_high = FloatOrNoneField()
    tp_low = FloatOrNoneField()
    tp_close = FloatOrNoneField()
    LS_open = FloatOrNoneField()
    LS_high = FloatOrNoneField()
    LS_low = FloatOrNoneField()
    LS_close = FloatOrNoneField()
    SL_open = FloatOrNoneField()
    SL_high = FloatOrNoneField()
    SL_low = FloatOrNoneField()
    SL_close = FloatOrNoneField()
    dollar = FloatOrNoneField(required=False)
    tp = FloatOrNoneField()
    scr = FloatOrNoneField()
    atp24h = FloatOrNoneField()
    converted_tp = FloatOrNoneField()
    closed = serializers.BooleanField()


class KlineVolatilityQueryParamsSerializer(serializers.Serializer):
    target_market_code = serializers.CharField(required=True)
    origin_market_code = serializers.CharField(required=True)
    base_asset = CharacterSeparatedField()
    tz = TimezoneField(default=UTC)


class KlineVolatilitySerializer(serializers.Serializer):
    base_asset = serializers.CharField()
    mean_diff = FloatOrNoneField()
    datetime_now = DateTimeWithTzField(
        format=DATE_TIME_TZ_FORMAT,
        default_timezone=TZ_UTC,
    )


class FundingRateDataQueryParamsSerializer(serializers.Serializer):
    market_code = serializers.CharField(required=True)
    base_asset = CharacterSeparatedField()
    last_n = serializers.IntegerField(
        default=1,
        required=False,
        help_text="Returns only the last n from the queried data."
        "-1 will return everything from the queried data.",
    )
    start_funding_time = serializers.DateTimeField(
        required=False,
        input_formats=[DATE_TIME_FORMAT],
        help_text="If start/end funding time is provided, "
        "initial queried data will be limited to that date range."
        "Otherwise, whole data will be queried.",
    )
    end_funding_time = serializers.DateTimeField(
        required=False,
        input_formats=[DATE_TIME_FORMAT],
        help_text="If start/end funding time is provided, "
        "initial queried data will be limited to that date range."
        "Otherwise, whole data will be queried.",
    )
    tz = TimezoneField(default=UTC)


class FundingRateDataSerializer(serializers.Serializer):
    symbol = serializers.CharField()
    funding_rate = FloatOrNoneField()
    funding_time = DateTimeWithTzField(
        format=DATE_TIME_TZ_FORMAT,
        default_timezone=TZ_UTC,
    )
    datetime_now = DateTimeWithTzField(
        format=DATE_TIME_TZ_FORMAT,
        default_timezone=TZ_UTC,
    )
    # base_asset = serializers.CharField()
    # quote_asset = serializers.CharField()
    # perpetual = serializers.BooleanField()


class AverageFundingRateDataQueryParamsSerializer(serializers.Serializer):
    n = serializers.IntegerField(
        required=True, validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    market_code = serializers.CharField(required=False)


class AverageFundingRateDataSerializer(serializers.Serializer):
    symbol = serializers.CharField()
    base_asset = serializers.CharField()
    quote_asset = serializers.CharField()
    market_code = serializers.CharField()
    funding_rate = FloatOrNoneField()


class FundingRateDiffDataQueryParamsSerializer(serializers.Serializer):
    market_code_x = serializers.CharField(required=False)
    exchange_x = serializers.CharField(required=False)
    market_code_y = serializers.CharField(required=False)
    exchange_y = serializers.CharField(required=False)
    tz = TimezoneField(default=UTC)


class FundingRateDiffDataSerializer(serializers.Serializer):
    base_asset = serializers.CharField()
    symbol_x = serializers.CharField()
    funding_rate_x = FloatOrNoneField()
    funding_time_x = DateTimeWithTzField(
        format=DATE_TIME_TZ_FORMAT,
        default_timezone=TZ_UTC,
    )
    quote_asset_x = serializers.CharField()
    market_code_x = serializers.CharField()
    exchange_x = serializers.CharField()
    symbol_y = serializers.CharField()
    funding_rate_y = FloatOrNoneField()
    funding_time_y = DateTimeWithTzField(
        format=DATE_TIME_TZ_FORMAT,
        default_timezone=TZ_UTC,
    )
    quote_asset_y = serializers.CharField()
    market_code_y = serializers.CharField()
    exchange_y = serializers.CharField()
    funding_rate_diff = FloatOrNoneField()


class WalletStatusQueryParamsSerializer(serializers.Serializer):
    target_market_code = serializers.CharField(required=True)
    origin_market_code = serializers.CharField(required=True)
    base_asset = CharacterSeparatedField()


class WalletStatusExchangeResponseSerializer(serializers.Serializer):
    deposit = serializers.ListField(child=serializers.CharField(default="network1"))
    withdraw = serializers.ListField(child=serializers.CharField(default="network1"))


class WalletStatusResponseSerializer(serializers.Serializer):
    base_asset1 = serializers.SerializerMethodField(method_name="get_base_asset")
    base_asset2 = serializers.SerializerMethodField(method_name="get_base_asset")

    @extend_schema_field(
        inline_serializer(
            name="WalletStatusBaseAssetResponseSerializer",
            fields={
                "target_exchange": WalletStatusExchangeResponseSerializer(),
                "origin_exchange": WalletStatusExchangeResponseSerializer(),
            },
        )
    )
    def get_base_asset(self, obj):
        pass


class RankIndicatorQueryParamsSerializer(serializers.Serializer):
    target_market_code = serializers.CharField(required=True)
    origin_market_code = serializers.CharField(required=True)
    tz = TimezoneField(default=UTC)
    w_ls_close = serializers.FloatField(required=False)
    w_spread = serializers.FloatField(required=False)
    w_volatility = serializers.FloatField(required=False)
    w_funding = serializers.FloatField(required=False)
    w_atp = serializers.FloatField(required=False)


class RankIndicatorSerializer(serializers.Serializer):
    base_asset = serializers.CharField()
    # Rank indicator values.
    indicator_value = serializers.IntegerField()


class AiRankRecommendationSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    base_asset = serializers.CharField()
    risk_level = serializers.IntegerField()
    explanation = serializers.CharField()
    datetime_now = DateTimeWithTzField(
        format=DATE_TIME_TZ_FORMAT,
        default_timezone=TZ_UTC,
    )


class AiRankRecommendationQueryParamsSerializer(serializers.Serializer):
    target_market_code = serializers.CharField(required=True)
    origin_market_code = serializers.CharField(required=True)


class VolatilityNotificationConfigSerializer(serializers.ModelSerializer):
    """Serializer for VolatilityNotificationConfig model."""

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = VolatilityNotificationConfig
        fields = [
            "id",
            "user",
            "target_market_code",
            "origin_market_code",
            "base_assets",
            "volatility_threshold",
            "notification_interval_minutes",
            "enabled",
            "last_notified_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "last_notified_at", "created_at", "updated_at"]

    def validate_base_assets(self, value):
        """Validate that base_assets is a list of strings if provided."""
        if value is not None:
            if not isinstance(value, list):
                raise serializers.ValidationError("base_assets must be a list")
            for asset in value:
                if not isinstance(asset, str):
                    raise serializers.ValidationError(
                        "Each item in base_assets must be a string"
                    )
        return value

    def validate(self, attrs):
        """Validate market code combination exists and user hasn't already configured it."""
        user = attrs.get("user") or self.context["request"].user
        target = attrs.get("target_market_code")
        origin = attrs.get("origin_market_code")

        # Check for duplicate config (only on create)
        if not self.instance:
            exists = VolatilityNotificationConfig.objects.filter(
                user=user,
                target_market_code=target,
                origin_market_code=origin,
            ).exists()

            if exists:
                raise serializers.ValidationError(
                    {
                        "non_field_errors": [
                            "You already have a notification config for this market combination."
                        ]
                    }
                )

        return attrs
