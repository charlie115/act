from django.db.models import Count
from rest_framework import exceptions, serializers

from lib.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_409_CONFLICT
from tradecore.mixins import TradeCoreMixin
from tradecore.models import Node, TradeConfigAllocation, EnabledMarketCodeCombination
from users.models import User


class NodeSerializer(serializers.ModelSerializer):
    market_code_combinations = serializers.SerializerMethodField(
        default=[],
        help_text="Returns a list of all the enabled market code combinations in the node.<br>"
        "Format:`{target}:{origin}`<br>"
        "Example: `UPBIT_SPOT/KRW:UPBIT_SPOT/BTC`",
    )

    def get_market_code_combinations(self, obj):
        market_code_combinations = [
            {
                "market_code_combination": f"{market_code_combination.target}:{market_code_combination.origin}",
                "trade_support": market_code_combination.trade_support,
            }
            for market_code_combination in obj.market_code_combinations.all()
        ]
        return market_code_combinations

    class Meta:
        model = Node
        fields = (
            "id",
            "name",
            "url",
            "description",
            "max_user_count",
            "market_code_combinations",
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


#######################
# For trade_core APIs #
#######################


class TradeConfigViewSetSerializer(TradeCoreMixin, serializers.Serializer):
    uuid = serializers.UUIDField(read_only=True)
    user = serializers.UUIDField(required=False)
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

    def validate(self, attrs):
        if self.instance is None:
            if "user" in attrs:
                try:
                    user = User.objects.get(uuid=attrs.get("user"))
                except User.DoesNotExist:
                    raise exceptions.ValidationError({"user": ["User not found."]})
            else:
                user = self.context["request"].user

            if user.telegram_chat_id is None:
                raise exceptions.ValidationError(
                    {"user": ["User is not connected to a telegram bot!"]}
                )

            attrs["user"] = user

        return attrs

    def create(self, validated_data):
        user = validated_data.pop("user")

        if self.is_not_yet_allocated(user, validated_data):
            validated_data["user"] = user.uuid
            validated_data["telegram_id"] = user.telegram_chat_id

            return self.allocate_user_trade(user, validated_data)

    def update(self, instance, validated_data):
        fixed_value_keys = [
            "user",
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

    def is_not_yet_allocated(self, user, data):
        try:
            user.trade_config_allocations.get(
                target_market_code=data.get("target_market_code"),
                origin_market_code=data.get("origin_market_code"),
            )
            exception = exceptions.APIException(
                {
                    "target_market_code": ["Trade config already exists."],
                    "origin_market_code": ["Trade config already exists."],
                }
            )
            exception.status_code = HTTP_409_CONFLICT
            raise exception

        except TradeConfigAllocation.DoesNotExist:
            return True

    def allocate_user_trade(self, user, data):
        nodes = (
            Node.objects.filter(
                market_code_combinations__target__code=data.get("target_market_code"),
                market_code_combinations__origin__code=data.get("origin_market_code"),
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


class TradesViewSetQueryParamsSerializer(TradeCoreMixin, serializers.Serializer):
    """Separate validation for query"""

    trade_config_uuid = serializers.UUIDField()

    def validate(self, attrs):
        trade_config_allocation = self.get_trade_config_allocation(
            attrs["trade_config_uuid"]
        )

        self.context["view"].check_object_permissions(
            request=self.context["request"],
            obj=trade_config_allocation,
        )

        return super().validate(attrs)


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
    last_trade_history_uuid = serializers.UUIDField(required=False)
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
    last_trade_history_uuid = serializers.UUIDField(required=False)
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


class TradeLogQueryParamsSerializer(TradeCoreMixin, serializers.Serializer):
    trade_config_uuid = serializers.UUIDField()

    def validate(self, attrs):
        trade_config_allocation = self.get_trade_config_allocation(
            attrs["trade_config_uuid"]
        )
        self.context["view"].check_object_permissions(
            request=self.context["request"],
            obj=trade_config_allocation,
        )

        return super().validate(attrs)


class TradeLogViewSetSerializer(TradeCoreMixin, serializers.Serializer):
    trade_config_uuid = serializers.UUIDField()
    trade_uuid = serializers.UUIDField(read_only=True)
    registered_datetime = serializers.DateTimeField(read_only=True)
    last_updated_datetime = serializers.DateTimeField(read_only=True)
    base_asset = serializers.CharField()
    usdt_conversion = serializers.BooleanField()
    low = serializers.FloatField()
    high = serializers.FloatField()
    trade_capital = serializers.FloatField(required=False)
    deleted = serializers.BooleanField()
    status = serializers.CharField(required=False)
    remark = serializers.CharField(required=False)


class ExchangeApiKeyViewSetQueryParamsSerializer(
    TradeCoreMixin, serializers.Serializer
):
    """Separate validation for query"""

    trade_config_uuid = serializers.UUIDField()

    def validate(self, attrs):
        trade_config_allocation = self.get_trade_config_allocation(
            attrs["trade_config_uuid"]
        )

        self.context["view"].check_object_permissions(
            request=self.context["request"],
            obj=trade_config_allocation,
        )

        return super().validate(attrs)


class ExchangeApiKeyViewSetSerializer(TradeCoreMixin, serializers.Serializer):
    trade_config_uuid = serializers.UUIDField()
    uuid = serializers.UUIDField(read_only=True)
    registered_datetime = serializers.DateTimeField(read_only=True)
    last_updated_datetime = serializers.DateTimeField(read_only=True)
    market_code = serializers.CharField()
    exchange = serializers.CharField(required=False)
    spot = serializers.BooleanField(required=False)
    futures = serializers.BooleanField(required=False)
    access_key = serializers.CharField()
    secret_key = serializers.CharField(write_only=True)
    passphrase = serializers.CharField(required=False, write_only=True)
    remark = serializers.CharField(required=False)

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


class CapitalQueryParamsSerializer(TradeCoreMixin, serializers.Serializer):
    trade_config_uuid = serializers.UUIDField()
    market_code = serializers.CharField()

    def validate(self, attrs):
        trade_config_allocation = self.get_trade_config_allocation(
            attrs["trade_config_uuid"]
        )
        self.context["view"].check_object_permissions(
            request=self.context["request"],
            obj=trade_config_allocation,
        )

        return super().validate(attrs)


class SpotPositionQueryParamsSerializer(TradeCoreMixin, serializers.Serializer):
    trade_config_uuid = serializers.UUIDField()
    market_code = serializers.CharField()

    def validate(self, attrs):
        trade_config_allocation = self.get_trade_config_allocation(
            attrs["trade_config_uuid"]
        )
        self.context["view"].check_object_permissions(
            request=self.context["request"],
            obj=trade_config_allocation,
        )

        return super().validate(attrs)


class FuturePositionQueryParamsSerializer(TradeCoreMixin, serializers.Serializer):
    trade_config_uuid = serializers.UUIDField()
    market_code = serializers.CharField()

    def validate(self, attrs):
        trade_config_allocation = self.get_trade_config_allocation(
            attrs["trade_config_uuid"]
        )
        self.context["view"].check_object_permissions(
            request=self.context["request"],
            obj=trade_config_allocation,
        )

        return super().validate(attrs)


class OrderHistoryQueryParamsSerializer(TradeCoreMixin, serializers.Serializer):
    trade_config_uuid = serializers.UUIDField()
    trade_uuid = serializers.UUIDField(required=False)

    def validate(self, attrs):
        trade_config_allocation = self.get_trade_config_allocation(
            attrs["trade_config_uuid"]
        )
        self.context["view"].check_object_permissions(
            request=self.context["request"],
            obj=trade_config_allocation,
        )

        return super().validate(attrs)


class OrderHistoryViewSetSerializer(TradeCoreMixin, serializers.Serializer):
    trade_config_uuid = serializers.UUIDField()
    trade_uuid = serializers.UUIDField()
    order_id = serializers.UUIDField(read_only=True)
    registered_datetime = serializers.DateTimeField(read_only=True)
    order_type = serializers.CharField()
    market_code = serializers.CharField()
    symbol = serializers.CharField()
    quote_asset = serializers.CharField()
    side = serializers.CharField()
    price = serializers.FloatField()
    qty = serializers.IntegerField()
    fee = serializers.FloatField()
    remark = serializers.CharField(required=False)


class TradeHistoryQueryParamsSerializer(TradeCoreMixin, serializers.Serializer):
    trade_config_uuid = serializers.UUIDField()
    trade_uuid = serializers.UUIDField(required=False)

    def validate(self, attrs):
        trade_config_allocation = self.get_trade_config_allocation(
            attrs["trade_config_uuid"]
        )
        self.context["view"].check_object_permissions(
            request=self.context["request"],
            obj=trade_config_allocation,
        )

        return super().validate(attrs)


class TradeHistoryViewSetFilterSerializer(serializers.Serializer):
    """
    This is just a hacky way to filter a non-model view
    Only used in overriden filter_queryset function of the corresponding view
    """

    base_asset = serializers.CharField(required=False)


class TradeHistoryViewSetSerializer(TradeCoreMixin, serializers.Serializer):
    trade_config_uuid = serializers.UUIDField()
    trade_uuid = serializers.UUIDField()
    uuid = serializers.UUIDField(read_only=True)
    registered_datetime = serializers.DateTimeField(read_only=True)
    trade_side = serializers.CharField()
    base_asset = serializers.CharField()
    target_order_id = serializers.CharField()  # uuid or string?
    origin_order_id = serializers.CharField()  # string?
    target_premium_value = serializers.IntegerField()  # integer?
    executed_premium_value = serializers.FloatField()
    slippage_p = serializers.FloatField()
    dollar = serializers.FloatField()
    remark = serializers.CharField(required=False)


class PNLHistoryQueryParamsSerializer(TradeCoreMixin, serializers.Serializer):
    trade_config_uuid = serializers.UUIDField()
    trade_uuid = serializers.UUIDField(required=False)

    def validate(self, attrs):
        trade_config_allocation = self.get_trade_config_allocation(
            attrs["trade_config_uuid"]
        )
        self.context["view"].check_object_permissions(
            request=self.context["request"],
            obj=trade_config_allocation,
        )

        return super().validate(attrs)


class PNLHistoryViewSetFilterSerializer(serializers.Serializer):
    """
    This is just a hacky way to filter a non-model view
    Only used in overriden filter_queryset function of the corresponding view
    """

    enter_trade_history_uuid = serializers.UUIDField(required=False)
    exit_trade_history_uuid = serializers.UUIDField(required=False)


class PNLHistoryViewSetSerializer(TradeCoreMixin, serializers.Serializer):
    trade_config_uuid = serializers.UUIDField()
    trade_uuid = serializers.UUIDField()
    uuid = serializers.UUIDField(read_only=True)
    registered_datetime = serializers.DateTimeField(read_only=True)
    market_code_combination = serializers.CharField()
    enter_trade_history_uuid = serializers.UUIDField()
    exit_trade_history_uuid = serializers.UUIDField()
    realized_premium_gap_p = serializers.FloatField()
    target_currency = serializers.CharField()
    target_pnl = serializers.FloatField()
    target_total_fee = serializers.FloatField()
    target_pnl_after_fee = serializers.FloatField()
    origin_currency = serializers.CharField()
    origin_pnl = serializers.FloatField()
    origin_total_fee = serializers.FloatField()
    origin_pnl_after_fee = serializers.FloatField()
    total_currency = serializers.CharField()
    total_pnl = serializers.FloatField()
    total_pnl_after_fee = serializers.FloatField()
    total_pnl_after_fee_kimp = serializers.FloatField()
    remark = serializers.CharField(required=False)


class PboundaryQueryParamsSerializer(TradeCoreMixin, serializers.Serializer):
    trade_config_uuid = serializers.UUIDField()
    market_code_combination = serializers.CharField()
    base_asset = serializers.CharField()
    usdt_conversion = serializers.BooleanField(required=True)
    percent_gap = serializers.FloatField()
    interval = serializers.CharField(default="1T")
    kline_num = serializers.IntegerField(default=200)

    def validate(self, attrs):
        trade_config_allocation = self.get_trade_config_allocation(
            attrs["trade_config_uuid"]
        )
        self.context["view"].check_object_permissions(
            request=self.context["request"],
            obj=trade_config_allocation,
        )

        return super().validate(attrs)

    def validate_market_code_combination(self, market_code_combination):
        market_code_combinations = [
            f"{enabled_market_code_combination.target}:{enabled_market_code_combination.origin}"
            for enabled_market_code_combination in EnabledMarketCodeCombination.objects.all()
        ]

        if market_code_combination not in market_code_combinations:
            raise exceptions.ValidationError

        return market_code_combination


class RepeatTradesViewSetQueryParamsSerializer(TradeCoreMixin, serializers.Serializer):
    trade_config_uuid = serializers.UUIDField()

    def validate(self, attrs):
        trade_config_allocation = self.get_trade_config_allocation(
            attrs["trade_config_uuid"]
        )

        self.context["view"].check_object_permissions(
            request=self.context["request"],
            obj=trade_config_allocation,
        )

        return super().validate(attrs)


class RepeatTradesViewSetFilterSerializer(serializers.Serializer):
    """
    This is just a hacky way to filter a non-model view
    Only used in overriden filter_queryset function of the corresponding view
    """

    trade_uuid = serializers.UUIDField(required=False)
    kline_interval = serializers.CharField(required=False)
    kline_num = serializers.IntegerField(required=False)
    pauto_num = serializers.FloatField(required=False)
    auto_repeat_switch = serializers.IntegerField(required=False)
    auto_repeat_num = serializers.IntegerField(required=False)
    status = serializers.CharField(required=False)


class RepeatTradesViewSetSerializer(TradeCoreMixin, serializers.Serializer):
    trade_config_uuid = serializers.UUIDField(write_only=True)
    trade_uuid = serializers.UUIDField()
    uuid = serializers.UUIDField(read_only=True)
    registered_datetime = serializers.DateTimeField(read_only=True)
    last_updated_datetime = serializers.DateTimeField(read_only=True)
    kline_interval = serializers.ChoiceField(
        default="1T", choices=["1T", "5T", "15T", "30T", "1H", "4H"], required=False
    )
    kline_num = serializers.IntegerField(required=False)
    pauto_num = serializers.FloatField(required=False)
    auto_repeat_switch = serializers.IntegerField()
    auto_repeat_num = serializers.IntegerField()
    status = serializers.CharField(required=False)
    remark = serializers.CharField(required=False)

    def create(self, validated_data):
        node = self.get_node(validated_data.pop("trade_config_uuid"))

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
            "trade_uuid",
        ]

        new_instance = instance.copy()
        for key, value in validated_data.items():
            if (
                key not in fixed_value_keys
                # Only update instance values if they are explicity provided in query
                and key in self.initial_data.keys()
                and value != instance.get(key, None)
            ):
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
