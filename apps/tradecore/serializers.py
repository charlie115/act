from django.db.models import Count
from rest_framework import exceptions, serializers

from lib.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_409_CONFLICT
from tradecore.mixins import TradeCoreMixin
from tradecore.models import Node, TradeConfigAllocation
from users.models import User


class NodeSerializer(serializers.ModelSerializer):
    market_code_services = serializers.SerializerMethodField(
        default=[],
        help_text="Returns a list of all the enabled market code services in the node.<br>"
        "Format:`{target}:{origin}`<br>"
        "Example: `UPBIT_SPOT/KRW:UPBIT_SPOT/BTC`",
    )

    def get_market_code_services(self, obj):
        market_code_services = [
            f"{market_code_service.target}:{market_code_service.origin}"
            for market_code_service in obj.market_code_services.all()
        ]
        return market_code_services

    class Meta:
        model = Node
        fields = (
            "id",
            "name",
            "url",
            "description",
            "max_user_count",
            "market_code_services",
        )


class TradeConfigAllocationSerializer(serializers.ModelSerializer):
    "TradeConfig serializer to be added to user details"

    class Meta:
        model = TradeConfigAllocation
        fields = (
            "target_market_code",
            "origin_market_code",
            "trade_config_uuid",
        )


class TradeConfigViewSetSerializer(TradeCoreMixin, serializers.Serializer):
    uuid = serializers.UUIDField(read_only=True)
    acw_user_uuid = serializers.UUIDField()
    telegram_id = serializers.IntegerField(read_only=True)
    target_market_code = serializers.CharField()
    origin_market_code = serializers.CharField()
    send_times = serializers.IntegerField(required=False)
    send_term = serializers.IntegerField(required=False)
    registered_datetime = serializers.DateTimeField(required=False)
    service_datetime_end = serializers.DateTimeField(required=False)
    target_market_uid = serializers.CharField(required=False)
    origin_market_uid = serializers.CharField(required=False)
    target_market_referral_use = serializers.BooleanField(required=False)
    origin_market_referral_use = serializers.BooleanField(required=False)
    target_market_cross = serializers.BooleanField(required=False)
    target_market_leverage = serializers.IntegerField(required=False)
    origin_market_cross = serializers.BooleanField(required=False)
    origin_market_leverage = serializers.IntegerField(required=False)
    target_market_margin_call = serializers.IntegerField(required=False)
    origin_market_margin_call = serializers.IntegerField(required=False)
    target_market_safe_reverse = serializers.BooleanField(required=False)
    origin_market_safe_reverse = serializers.BooleanField(required=False)
    target_market_risk_threshold_p = serializers.FloatField(required=False)
    origin_market_risk_threshold_p = serializers.FloatField(required=False)
    repeat_limit_p = serializers.FloatField(required=False)
    repeat_limit_direction = serializers.CharField(required=False)
    repeat_num_limit = serializers.IntegerField(required=False)
    on_off = serializers.BooleanField(required=False)
    remark = serializers.CharField(required=False)

    def create(self, validated_data):
        try:
            user = User.objects.get(uuid=validated_data.get("acw_user_uuid"))
            self.check_existing_allocation(user, validated_data)

        except User.DoesNotExist:
            raise exceptions.ValidationError({"user": ["User not found."]})

        except TradeConfigAllocation.DoesNotExist:
            validated_data["telegram_id"] = user.telegram_chat_id
            return self.allocate_user_trade(user, validated_data)

    def update(self, instance, validated_data):
        fixed_value_keys = [
            "user_uuid",
            "telegram_id",
            "target_market_code",
            "origin_market_code",
        ]

        new_instance = instance.copy()
        for key, value in validated_data.items():
            if key not in fixed_value_keys and value != instance.get(key, None):
                new_instance[key] = value

        node = self.get_node(instance.get("uuid"))

        api_response = self.tradecore_update_api(
            url=node.url,
            endpoint=self.context["view"].tradecore_api_endpoint,
            path_param=instance.get("uuid"),
            data=new_instance,
        )

        if api_response.status_code == HTTP_200_OK:
            return api_response.json()

        self.handle_exception_from_api(api_response)

    def check_existing_allocation(self, user, data):
        trade_config_allocation = user.trade_config_allocations.get(
            target_market_code=data.get("target_market_code"),
            origin_market_code=data.get("origin_market_code"),
        )
        if trade_config_allocation:
            exception = exceptions.APIException(
                {
                    "target_market_code": ["Trade config already exists."],
                    "origin_market_code": ["Trade config already exists."],
                }
            )
            exception.status_code = HTTP_409_CONFLICT
            raise exception

    def allocate_user_trade(self, user, data):
        nodes = (
            Node.objects.filter(
                market_code_services__target__code=data.get("target_market_code"),
                market_code_services__origin__code=data.get("origin_market_code"),
            )
            .annotate(user_count=Count("users"))
            .order_by("user_count", "id")
        )
        if len(nodes) > 0:
            node = nodes.first()

            api_response = self.tradecore_create_api(
                url=node.url,
                endpoint=self.context["view"].tradecore_api_endpoint,
                data=data,
            )
            if api_response.status_code == HTTP_201_CREATED:
                instance = api_response.json()

                node.users.add(user)
                TradeConfigAllocation.objects.create(
                    node=node,
                    target_market_code=data["target_market_code"],
                    origin_market_code=data["origin_market_code"],
                    user=user,
                    trade_config_uuid=instance.get("uuid"),
                )

                return instance

            self.handle_exception_from_api(api_response)

        raise exceptions.ValidationError(
            {"node": "Node not found for the selected market combination."}
        )


class TradesViewSetQueryParamsSerializer(serializers.Serializer):
    trade_config_uuid = serializers.UUIDField()


class TradesViewSetFilterSerializer(serializers.Serializer):
    """
    This is just a hacky way to filter a non-model view
    Only used in overriden filter_queryset function of the corresponding view
    """

    base_asset = serializers.CharField(required=False)
    usdt_conversion = serializers.BooleanField(required=False)
    low = serializers.IntegerField(required=False)
    high = serializers.IntegerField(required=False)
    trigger_switch = serializers.IntegerField(required=False)
    trade_switch = serializers.IntegerField(required=False)
    trade_capital = serializers.IntegerField(required=False)
    enter_target_market_order_id = serializers.CharField(required=False)
    enter_origin_market_order_id = serializers.CharField(required=False)
    exit_target_market_order_id = serializers.CharField(required=False)
    exit_origin_market_order_id = serializers.CharField(required=False)
    status = serializers.CharField(required=False)
    remark = serializers.CharField(required=False)


class TradesViewSetSerializer(TradeCoreMixin, serializers.Serializer):
    trade_config_uuid = serializers.UUIDField()
    uuid = serializers.UUIDField(read_only=True)
    base_asset = serializers.CharField()
    usdt_conversion = serializers.BooleanField()
    low = serializers.FloatField()
    high = serializers.FloatField()
    registered_datetime = serializers.DateTimeField(read_only=True)
    last_updated_datetime = serializers.DateTimeField(read_only=True)
    trigger_switch = serializers.IntegerField(required=False)
    trade_switch = serializers.IntegerField(required=False)
    trade_capital = serializers.FloatField(required=False)
    enter_target_market_order_id = serializers.CharField(required=False)
    enter_origin_market_order_id = serializers.CharField(required=False)
    exit_target_market_order_id = serializers.CharField(required=False)
    exit_origin_market_order_id = serializers.CharField(required=False)
    status = serializers.CharField(required=False)
    remark = serializers.CharField(required=False)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not attrs["low"] < attrs["high"]:
            raise exceptions.ValidationError({"low": ["Low must be less than high."]})

        return attrs

    def create(self, validated_data):
        node = self.get_node(validated_data.get("trade_config_uuid"))

        api_response = self.tradecore_create_api(
            url=node.url,
            endpoint=self.context["view"].tradecore_api_endpoint,
            data=validated_data,
        )

        if api_response.status_code == HTTP_201_CREATED:
            return api_response.json()

        self.handle_exception_from_api(api_response)

    def update(self, instance, validated_data):
        fixed_value_keys = [
            "trade_config_uuid",
            "base_asset",
        ]

        new_instance = instance.copy()
        for key, value in validated_data.items():
            if key not in fixed_value_keys and value != instance.get(key, None):
                new_instance[key] = value

        node = self.get_node(validated_data.get("trade_config_uuid"))

        api_response = self.tradecore_update_api(
            url=node.url,
            endpoint=self.context["view"].tradecore_api_endpoint,
            path_param=instance.get("uuid"),
            data=new_instance,
        )

        if api_response.status_code == HTTP_200_OK:
            return api_response.json()

        self.handle_exception_from_api(api_response)
