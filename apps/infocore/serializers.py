from rest_framework import serializers

from lib.constants import DATE_TIME_FORMAT


class KlineDataQueryParamsSerializer(serializers.Serializer):
    target_market_code = serializers.CharField(required=True)
    origin_market_code = serializers.CharField(required=True)
    base_asset = serializers.CharField(required=True)
    interval = serializers.CharField(required=True)
    start_time = serializers.DateTimeField(
        required=True,
        input_formats=[DATE_TIME_FORMAT],
    )
    end_time = serializers.DateTimeField(
        required=True,
        input_formats=[DATE_TIME_FORMAT],
    )


class KlineDataDataSerializer(serializers.Serializer):
    base_asset = serializers.CharField()
    datetime_now = serializers.DateTimeField()
    tp_open = serializers.FloatField()
    tp_high = serializers.FloatField()
    tp_low = serializers.FloatField()
    tp_close = serializers.FloatField()
    LS_open = serializers.FloatField()
    LS_high = serializers.FloatField()
    LS_low = serializers.FloatField()
    LS_close = serializers.FloatField()
    SL_open = serializers.FloatField()
    SL_high = serializers.FloatField()
    SL_low = serializers.FloatField()
    SL_close = serializers.FloatField()
    dollar = serializers.FloatField()
    tp = serializers.FloatField()
    scr = serializers.FloatField()
    atp24h = serializers.FloatField()
    converted_tp = serializers.FloatField()
    closed = serializers.BooleanField()
