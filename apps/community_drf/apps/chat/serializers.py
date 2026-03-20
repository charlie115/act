from rest_framework import serializers

from lib.datetime import DATE_TIME_FORMAT, DATE_TIME_TZ_FORMAT, UTC, TZ_UTC
from lib.fields import DateTimeWithTzField, TimezoneField


class PastChatMessagesQueryParamsSerializer(serializers.Serializer):
    start_time = serializers.DateTimeField(
        required=False,
        input_formats=[DATE_TIME_FORMAT],
    )
    end_time = serializers.DateTimeField(
        required=False,
        input_formats=[DATE_TIME_FORMAT],
    )
    tz = TimezoneField(default=UTC)


class PastChatMessagesSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, default="")
    username = serializers.CharField()
    # ip = serializers.IPAddressField()
    message = serializers.CharField()
    datetime = DateTimeWithTzField(
        format=DATE_TIME_TZ_FORMAT,
        default_timezone=TZ_UTC,
    )
    is_anon = serializers.BooleanField(required=False, default=False)
