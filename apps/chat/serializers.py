from rest_framework import serializers
from pytz import all_timezones, timezone

from lib.datetime import DATE_TIME_FORMAT, DATE_TIME_TZ_FORMAT, UTC


class PastChatMessagesQueryParamsSerializer(serializers.Serializer):
    start_time = serializers.DateTimeField(
        required=False,
        input_formats=[DATE_TIME_FORMAT],
    )
    end_time = serializers.DateTimeField(
        required=False,
        input_formats=[DATE_TIME_FORMAT],
    )
    tz = serializers.ChoiceField(choices=all_timezones, default=UTC)


class PastChatMessagesSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField()
    # ip = serializers.IPAddressField()
    message = serializers.CharField()
    datetime = serializers.DateTimeField()

    def to_representation(self, instance):
        instance["datetime"] = instance["datetime"].astimezone(
            timezone(self.context["tz"])
        )
        data = super().to_representation(instance)
        data["datetime"] = instance["datetime"].strftime(DATE_TIME_TZ_FORMAT)
        return data
