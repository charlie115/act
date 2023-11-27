from django.core.validators import MinValueValidator, MaxValueValidator
from drf_spectacular.utils import extend_schema_field, inline_serializer
from rest_framework import serializers
from pytz import all_timezones, timezone

from infocore.mixins import AssetMixin
from infocore.models import Asset
from lib.datetime import DATE_TIME_FORMAT, DATE_TIME_TZ_FORMAT, UTC, TZ_UTC
from lib.fields import CharacterSeparatedField, FloatOrNoneField


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
    tz = serializers.ChoiceField(choices=all_timezones, default=UTC)


class KlineDataSerializer(serializers.Serializer):
    base_asset = serializers.CharField()
    datetime_now = serializers.DateTimeField()
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

    def to_representation(self, instance):
        instance["datetime_now"] = instance["datetime_now"].astimezone(
            timezone(self.context["tz"])
        )
        data = super().to_representation(instance)
        data["datetime_now"] = instance["datetime_now"].strftime(DATE_TIME_TZ_FORMAT)
        return data


class FundingRateDataQueryParamsSerializer(serializers.Serializer):
    market_code = serializers.CharField(required=True)
    base_asset = CharacterSeparatedField(required=False, empty=True)
    tz = serializers.ChoiceField(choices=all_timezones, default=UTC)


class FundingRateDataSerializer(serializers.Serializer):
    symbol = serializers.CharField()
    funding_rate = FloatOrNoneField()
    funding_time = serializers.DateTimeField(default_timezone=TZ_UTC)
    base_asset = serializers.CharField()
    quote_asset = serializers.CharField()
    perpetual = serializers.BooleanField()
    datetime_now = serializers.DateTimeField(default_timezone=TZ_UTC)

    def to_representation(self, instance):
        instance["funding_time"] = instance["funding_time"].astimezone(
            timezone(self.context["tz"])
        )
        instance["datetime_now"] = instance["datetime_now"].astimezone(
            timezone(self.context["tz"])
        )

        data = super().to_representation(instance)

        data["funding_time"] = instance["funding_time"].strftime(DATE_TIME_TZ_FORMAT)
        data["datetime_now"] = instance["datetime_now"].strftime(DATE_TIME_TZ_FORMAT)

        return data


class AverageFundingRateDataQueryParamsSerializer(serializers.Serializer):
    n = serializers.IntegerField(
        required=True, validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    market_code = serializers.CharField(required=False)
    base_asset = CharacterSeparatedField(required=False, empty=True)


class AverageFundingRateDataSerializer(serializers.Serializer):
    symbol = serializers.CharField()
    base_asset = serializers.CharField()
    quote_asset = serializers.CharField()
    market_code = serializers.CharField()
    funding_rate = FloatOrNoneField()


class FundingRateDiffDataQueryParamsSerializer(serializers.Serializer):
    base_asset = CharacterSeparatedField(required=False, empty=True)
    market_code_x = serializers.CharField(required=False)
    exchange_x = serializers.CharField(required=False)
    market_code_y = serializers.CharField(required=False)
    exchange_y = serializers.CharField(required=False)
    tz = serializers.ChoiceField(choices=all_timezones, default=UTC)


class FundingRateDiffDataSerializer(serializers.Serializer):
    base_asset = serializers.CharField()
    symbol_x = serializers.CharField()
    funding_rate_x = FloatOrNoneField()
    funding_time_x = serializers.DateTimeField(default_timezone=TZ_UTC)
    quote_asset_x = serializers.CharField()
    market_code_x = serializers.CharField()
    exchange_x = serializers.CharField()
    symbol_y = serializers.CharField()
    funding_rate_y = FloatOrNoneField()
    funding_time_y = serializers.DateTimeField(default_timezone=TZ_UTC)
    quote_asset_y = serializers.CharField()
    market_code_y = serializers.CharField()
    exchange_y = serializers.CharField()
    funding_rate_diff = FloatOrNoneField()


class WalletStatusQueryParamsSerializer(serializers.Serializer):
    target_market_code = serializers.CharField(required=True)
    origin_market_code = serializers.CharField(required=True)
    base_asset = CharacterSeparatedField(required=False, empty=True)


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
