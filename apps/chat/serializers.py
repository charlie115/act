from rest_framework import serializers
from pytz import all_timezones

from lib.datetime import TZ_ASIA_SEOUL, DATE_TIME_FORMAT


class PastChatMessagesQueryParamsSerializer(serializers.Serializer):
    start_time = serializers.DateTimeField(
        required=False,
        input_formats=[DATE_TIME_FORMAT],
    )
    end_time = serializers.DateTimeField(
        required=False,
        input_formats=[DATE_TIME_FORMAT],
    )
    tz = serializers.ChoiceField(choices=all_timezones, default=TZ_ASIA_SEOUL)


class PastChatMessagesSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField()
    ip = serializers.IPAddressField()
    message = serializers.CharField()
    datetime = serializers.DateTimeField()
