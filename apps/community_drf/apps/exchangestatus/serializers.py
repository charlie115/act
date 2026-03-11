from rest_framework import serializers
from .models import ExchangeServerStatus

class ExchangeServerStatusSerializer(serializers.ModelSerializer):
    market_code = serializers.CharField(source='market_code.code', read_only=True)
    server_check = serializers.SerializerMethodField()

    class Meta:
        model = ExchangeServerStatus
        fields = ['id', 'market_code', 'start_time', 'end_time', 'message', 'server_check']
        read_only_fields = ['id', 'market_code', 'server_check']

    def get_server_check(self, obj):
        return obj.server_check