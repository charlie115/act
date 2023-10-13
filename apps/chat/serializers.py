from rest_framework import serializers

from lib.datetime import DATE_TIME_FORMAT


class PastChatMessagesQueryParamsSerializer(serializers.Serializer):
    start_time = serializers.DateTimeField(
        required=False,
        input_formats=[DATE_TIME_FORMAT],
    )
    end_time = serializers.DateTimeField(
        required=False,
        input_formats=[DATE_TIME_FORMAT],
    )


class PastChatMessagesSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField()
    ip = serializers.IPAddressField()
    message = serializers.CharField()
    datetime = serializers.DateTimeField()
