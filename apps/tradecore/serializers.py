from datetime import datetime, timezone
from rest_framework import exceptions, serializers

from lib.datetime import ONE_DAY_IN_SECONDS
from tradecore.mixins import NodeValidatorMixin
from tradecore.models import Node, UserConfig
from users.mixins import UserUUIDSerializerMixin


class NodeSerializer(NodeValidatorMixin, serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = (
            "id",
            "name",
            "domain",
            "port",
            "telegram_bot_id",
            "telegram_bot_token",
            "description",
        )


class UserConfigSerializer(UserUUIDSerializerMixin, serializers.ModelSerializer):
    node = serializers.SerializerMethodField()

    def get_node(self, obj):
        return obj.user.node.id

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

    def create(self, validated_data):
        if (
            hasattr(validated_data["user"], "trade_config")
            and validated_data["user"].trade_config
        ):
            raise exceptions.ValidationError(
                {
                    "user": f"{validated_data['user']} already has a trade configuration set."
                }
            )
        if validated_data["user"].node is None:
            raise exceptions.ValidationError(
                {"user": f"{validated_data['user']} is not assigned to a Node yet."}
            )
        return super().create(validated_data)

    class Meta:
        model = UserConfig
        fields = (
            "id",
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
            "user": {"read_only": True},
        }
