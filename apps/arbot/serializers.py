from django.db.models import Count
from rest_framework import serializers

from arbot.mixins import ArbotNodeValidatorMixin
from arbot.models import ArbotNode, ArbotUserConfig
from users.mixins import UserUUIDSerializerMixin


class ArbotNodeSerializer(ArbotNodeValidatorMixin, serializers.ModelSerializer):
    class Meta:
        model = ArbotNode
        fields = (
            "name",
            "domain",
            "port",
            "telegram_bot_id",
            "telegram_bot_token",
            "description",
            "user_configs",
        )
        extra_kwargs = {
            "user_configs": {"read_only": True},
        }


class ArbotUserConfigSerializer(UserUUIDSerializerMixin, serializers.ModelSerializer):
    def validate(self, attrs):
        nodes = (
            ArbotNode.objects.all()
            .annotate(config_count=Count("user_configs"))
            .order_by("config_count", "id")
        )
        attrs["node"] = nodes.first()

        return super().validate(attrs)

    class Meta:
        model = ArbotUserConfig
        fields = (
            "user",
            "node",
            "service_expiry_date",
            "addcir_limit",
            "addcir_num_limit",
            "binance_leverage",
            "binance_cross",
            "risk_warning_mode",
            "risk_warning_threshold_p",
            "safe_reverse",
            "alarm_num",
            "alarm_term_sec",
        )
        extra_kwargs = {
            "node": {"read_only": True},
        }
