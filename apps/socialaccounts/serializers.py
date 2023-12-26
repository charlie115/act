from rest_framework import serializers

from socialaccounts.models import ProxySocialApp


class ProxySocialAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProxySocialApp
        fields = (
            "id",
            "provider",
            "name",
            # "client_id",
            # "secret",
            # "key",
        )
