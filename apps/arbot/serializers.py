from datetime import datetime, timezone
from django.db.models import Count
from rest_framework import exceptions, serializers

from arbot.mixins import ArbotNodeValidatorMixin
from arbot.models import ArbotNode, ArbotUserConfig
from lib.datetime import ONE_DAY_IN_SECONDS
from users.mixins import UserUUIDSerializerMixin


class ArbotNodeSerializer(ArbotNodeValidatorMixin, serializers.ModelSerializer):
    class Meta:
        model = ArbotNode
        fields = (
            "id",
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
    def validate_service_expiry_date(self, service_expiry_date):
        if service_expiry_date <= datetime.now(tz=timezone.utc):
            raise exceptions.ValidationError(
                "Service expiry date can't be in the past."
            )

        if (
            service_expiry_date - datetime.now(tz=timezone.utc)
        ).total_seconds() < ONE_DAY_IN_SECONDS:
            raise exceptions.ValidationError(
                "Service expiry date can't be less than 1 day."
            )
        return service_expiry_date

    def validate(self, attrs):
        nodes = (
            ArbotNode.objects.all()
            .annotate(config_count=Count("user_configs"))
            .order_by("config_count", "id")
        )

        if len(nodes) > 0:
            attrs["node"] = nodes.first()
        else:
            raise exceptions.ValidationError(
                {"detail": "There is no Node to create configurations!"}
            )

        return super().validate(attrs)

    class Meta:
        model = ArbotUserConfig
        fields = (
            "id",
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
