from rest_framework import serializers


class TimestampField(serializers.Field):
    def to_representation(self, value):
        return round(value.timestamp() * 1000)


class InfoCoreHistoricalCoinDataQueryParamsSerializer(serializers.Serializer):
    exchange_market_1 = serializers.CharField(
        required=True, help_text="Base exchange market"
    )
    exchange_market_2 = serializers.CharField(
        required=True, help_text="Target exchange market"
    )
    period = serializers.CharField(required=True)
    coin = serializers.CharField(required=True)


class InfoCoreHistoricalCoinDataSerializer(serializers.Serializer):
    base_asset = serializers.CharField()
    datetime_now = TimestampField()
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
