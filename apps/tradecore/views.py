from django.core.cache import cache
from django.db.models import CharField, Value
from django.db.models.functions import Concat
from django_filters import CharFilter, FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import exceptions, mixins, response, views, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter

from lib.authentication import NodeIPAuthentication
from lib.filters import filter_list_of_dictionaries
from lib.permissions import IsAdmin, IsInternal, IsManager, IsUser
from lib.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND
from lib.views import BaseViewSet
from tradecore.mixins import TradeCoreMixin
from tradecore.models import Node
from tradecore.serializers import (
    NodeSerializer,
    TradeConfigViewSetSerializer,
    TradesViewSetQueryParamsSerializer,
    TradesViewSetFilterSerializer,
    TradesViewSetSerializer,
    TradeLogQueryParamsSerializer,
    TradeLogViewSetSerializer,
    RepeatTradesViewSetQueryParamsSerializer,
    RepeatTradesViewSetFilterSerializer,
    RepeatTradesViewSetSerializer,
    ExchangeApiKeyViewSetQueryParamsSerializer,
    ExchangeApiKeyViewSetSerializer,
    CapitalQueryParamsSerializer,
    SpotPositionQueryParamsSerializer,
    FuturePositionQueryParamsSerializer,
    OrderHistoryQueryParamsSerializer,
    OrderHistoryViewSetSerializer,
    TradeHistoryQueryParamsSerializer,
    TradeHistoryViewSetFilterSerializer,
    TradeHistoryViewSetSerializer,
    PNLHistoryQueryParamsSerializer,
    PNLHistoryViewSetFilterSerializer,
    PNLHistoryViewSetSerializer,
    PboundaryQueryParamsSerializer,
    ExitTradeQueryParamsSerializer,
    TriggerScannerQueryParamsSerializer,
    TriggerScannerFilterSerializer,
    TriggerScannerViewSetSerializer,
)


class NodeFilter(FilterSet):
    description__contains = CharFilter(field_name="description", lookup_expr="contains")
    market_code_combinations = CharFilter(
        field_name="market_code_combinations",
        method="filter_market_code",
        help_text="Filter from a list of enabled market code combinations in the node.<br>"
        "Format:`{target}:{origin}`<br>"
        "Example: `UPBIT_SPOT/KRW:UPBIT_SPOT/BTC`",
    )

    def filter_market_code(self, queryset, name, value):
        return queryset.annotate(
            market_code=Concat(
                "market_code_combinations__target__code",
                Value(":"),
                "market_code_combinations__origin__code",
                output_field=CharField(),
            )
        ).filter(market_code=value)

    class Meta:
        model = Node
        fields = (
            "name",
            "url",
            "description",
            "max_user_count",
            "market_code_combinations",
        )


@extend_schema(tags=["Node"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List nodes",
        description="Returns a list of all  `nodes`.",
    ),
    create=extend_schema(
        operation_id="Create a node",
        description="Creates a new `node`.",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve a node",
        description="Retrieves the details of an existing `node`.",
    ),
    update=extend_schema(
        operation_id="Fully update an node",
        description="Fully updates an existing `node`.<br>"
        "*All the previous values of the `node` will be replaced with the new values provided. "
        "Any parameters not provided will be unset.*",
    ),
    partial_update=extend_schema(
        operation_id="Update an node",
        description="Updates an existing ` node`.<br>"
        "*Only the parameters specified will be updated while the rest will be left unchanged.*",
    ),
    destroy=extend_schema(
        operation_id="Delete a node",
        description="Deletes an existing `node`.",
    ),
)
class NodeViewSet(BaseViewSet):
    queryset = Node.objects.all()
    serializer_class = NodeSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = NodeFilter
    ordering_fields = ["id", "name"]
    ordering = ["id"]
    http_method_names = ["get", "post", "put", "patch", "delete"]

    def get_authenticators(self):
        authentication_classes = self.authentication_classes + [NodeIPAuthentication]
        return [auth() for auth in authentication_classes]

    def get_permissions(self):
        permission_classes = self.permission_classes

        if (
            hasattr(self.request, "_authenticator")
            and type(self.request._authenticator) is NodeIPAuthentication
        ):
            permission_classes = []

        return [permission() for permission in permission_classes]
    


###################
# trade_core APIs #
###################


@extend_schema_view(
    retrieve=extend_schema(
        operation_id="Retrieve a trade config",
        description="Retrieves the details of an existing `trade config`.",
        tags=["TradeConfig"],
    ),
    create=extend_schema(
        operation_id="Create a trade config",
        description="Creates a new `trade config`.",
        tags=["TradeConfig"],
    ),
    update=extend_schema(
        operation_id="Fully update a trade config",
        description="Fully updates an existing `trade config`.<br>"
        "*All the previous values of the `trade config` will be replaced with the new values provided. "
        "Any parameters not provided will be unset.*",
        tags=["TradeConfig"],
    ),
    destroy=extend_schema(
        operation_id="Delete a trade config",
        description="Deletes an existing `trade config`.",
        tags=["TradeConfig"],
    ),
)
class TradeConfigViewSet(
    TradeCoreMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TradeConfigViewSetSerializer
    permission_classes = [IsAdmin | IsInternal | IsManager | IsUser]
    lookup_field = "uuid"
    tradecore_api_endpoint = "trade-config/"
    http_method_names = ["get", "post", "put", "delete"]

    def get_object(self):
        "Override get_object since our queryset is a dict and not a model"

        trade_config_allocation = self.get_trade_config_allocation(
            trade_config_uuid=self.kwargs[self.lookup_field],
            detail=True,
        )
        node = trade_config_allocation.node

        api_response = self.tradecore_retrieve_api(
            url=node.url,
            endpoint=self.tradecore_api_endpoint,
            path_param=trade_config_allocation.trade_config_uuid,
        )
        if api_response.status_code == HTTP_200_OK:
            obj = api_response.json()
            self.check_object_permissions(self.request, obj)
            return obj

        self.handle_exception_from_api(api_response)

    def perform_create(self, serializer):
        self.check_object_permissions(self.request, dict(serializer.validated_data))
        serializer.save()

    def perform_destroy(self, instance):
        trade_config_allocation = self.get_trade_config_allocation(
            trade_config_uuid=instance.get(self.lookup_field),
            detail=True,
        )
        node = trade_config_allocation.node

        api_response = self.tradecore_destroy_api(
            url=node.url,
            endpoint=self.tradecore_api_endpoint,
            path_param=instance.get(self.lookup_field),
        )

        if api_response.status_code == HTTP_204_NO_CONTENT:
            trade_config_allocation.delete()
            return response.Response(status=HTTP_204_NO_CONTENT)

        self.handle_exception_from_api(api_response)


@extend_schema(tags=["Trade"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List trades",
        description="Returns a list of all  `trades`.",
    ),
    create=extend_schema(
        operation_id="Create a trade",
        description="Creates a new `trade`.",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve a trade",
        description="Retrieves the details of an existing `trade`.",
    ),
    destroy=extend_schema(
        operation_id="Delete a trade",
        description="Deletes an existing `trade`.",
    ),
    delete=extend_schema(
        operation_id="Delete all user trades",
        description="Deletes all `trades` of a user.",
    ),
)
class TradesViewSet(
    TradeCoreMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TradesViewSetSerializer
    permission_classes = [IsAdmin | IsInternal | IsManager | IsUser]
    lookup_field = "uuid"
    tradecore_api_endpoint = "trades/"
    http_method_names = ["get", "post", "put", "delete"]

    def get_object(self):
        "Override get_object since our queryset is a dict and not a model"

        queryset = self.filter_queryset(self.get_queryset())

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            "Expected view %s to be called with a URL keyword argument "
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            "attribute on the view correctly."
            % (self.__class__.__name__, lookup_url_kwarg)
        )

        obj = next(
            (
                item
                for item in queryset
                if item[self.lookup_field] == self.kwargs[lookup_url_kwarg]
            ),
            None,
        )

        if obj is None:
            raise exceptions.NotFound()

        return obj

    def filter_queryset(self, queryset):
        filterset = super().filter_queryset(queryset)

        query_params = TradesViewSetFilterSerializer(data=self.request.query_params)
        query_params.is_valid(raise_exception=True)

        query = {
            key: value
            for key, value in query_params.validated_data.items()
            if key in self.request.query_params.keys()
        }

        filterset = filter_list_of_dictionaries(query, queryset)

        return filterset

    def get_queryset(self):
        query_params = TradesViewSetQueryParamsSerializer(
            context={"view": self, "request": self.request},
            data=self.request.query_params,
        )
        query_params.is_valid(raise_exception=True)
        query = query_params.validated_data

        node = self.get_node(trade_config_uuid=query.get("trade_config_uuid"))

        api_response = self.tradecore_list_api(
            url=node.url,
            endpoint=self.tradecore_api_endpoint,
            query_params=query,
        )

        if api_response.status_code == HTTP_200_OK:
            return api_response.json()

        self.handle_exception_from_api(api_response)

    def perform_create(self, serializer):
        trade_config_allocation = self.get_trade_config_allocation(
            serializer.validated_data["trade_config_uuid"]
        )
        self.check_object_permissions(self.request, trade_config_allocation)
        serializer.save()

    def delete(self, request, *args, **kwargs):
        if not kwargs:
            return self.bulk_delete(request)
        return self.destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        node = self.get_node(trade_config_uuid=instance.get("trade_config_uuid"))

        api_response = self.tradecore_destroy_api(
            url=node.url,
            endpoint=self.tradecore_api_endpoint,
            path_param=instance.get(self.lookup_field),
        )

        if api_response.status_code == HTTP_204_NO_CONTENT:
            return response.Response(status=HTTP_204_NO_CONTENT)

        self.handle_exception_from_api(api_response)

    @extend_schema(responses=TradesViewSetSerializer(many=True))
    @action(detail=False, methods=["delete"])
    def bulk_delete(self, request):
        query_params = TradesViewSetQueryParamsSerializer(
            context={"view": self, "request": self.request},
            data=self.request.query_params,
        )
        query_params.is_valid(raise_exception=True)
        query = query_params.validated_data

        node = self.get_node(trade_config_uuid=query.get("trade_config_uuid"))

        api_response = self.tradecore_destroy_many_api(
            url=node.url,
            endpoint=self.tradecore_api_endpoint,
            query_params=query,
        )

        if api_response.status_code == HTTP_204_NO_CONTENT:
            return response.Response(status=HTTP_204_NO_CONTENT)
        elif api_response.status_code == HTTP_404_NOT_FOUND:
            raise exceptions.NotFound(api_response.json().get("detail"))

        self.handle_exception_from_api(api_response)


@extend_schema(tags=["TradeLog"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List trade logs",
        description="Returns a list of all `trade logs`.",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve a trade log",
        description="Retrieves the details of an existing `trade log`.",
    ),
)
class TradeLogViewSet(
    TradeCoreMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TradeLogViewSetSerializer
    permission_classes = [IsAdmin | IsInternal | IsManager | IsUser]
    lookup_field = "trade_uuid"
    tradecore_api_endpoint = "trade-log/"
    http_method_names = ["get"]

    def get_object(self):
        "Override get_object since our queryset is a dict and not a model"

        queryset = self.filter_queryset(self.get_queryset())

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            "Expected view %s to be called with a URL keyword argument "
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            "attribute on the view correctly."
            % (self.__class__.__name__, lookup_url_kwarg)
        )

        obj = next(
            (
                item
                for item in queryset
                if item[self.lookup_field] == self.kwargs[lookup_url_kwarg]
            ),
            None,
        )

        if obj is None:
            raise exceptions.NotFound()

        return obj

    def get_queryset(self):
        query_params = TradeLogQueryParamsSerializer(
            context={"view": self, "request": self.request},
            data=self.request.query_params,
        )
        query_params.is_valid(raise_exception=True)
        query = query_params.validated_data

        node = self.get_node(trade_config_uuid=query.get("trade_config_uuid"))

        api_response = self.tradecore_list_api(
            url=node.url,
            endpoint=self.tradecore_api_endpoint,
            query_params=query,
        )

        if api_response.status_code == HTTP_200_OK:
            return api_response.json()

        self.handle_exception_from_api(api_response)


@extend_schema(tags=["RepeatTrades"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List repeat trades",
        description="Returns a list of all  `repeat trades`.",
    ),
    create=extend_schema(
        operation_id="Create a repeat trade",
        description="Creates a new `repeat trade`.",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve a repeat trade",
        description="Retrieves the details of an existing `repeat trade`.",
    ),
    destroy=extend_schema(
        operation_id="Delete a repeat trade",
        description="Deletes an existing `repeat trade`.",
    ),
)
class RepeatTradesViewSet(
    TradeCoreMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = RepeatTradesViewSetSerializer
    permission_classes = [IsAdmin | IsInternal | IsManager | IsUser]
    lookup_field = "uuid"
    tradecore_api_endpoint = "repeat-trades/"
    http_method_names = ["get", "post", "put", "delete"]

    def get_object(self):
        "Override get_object since our queryset is a dict and not a model"

        queryset = self.filter_queryset(self.get_queryset())

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            "Expected view %s to be called with a URL keyword argument "
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            "attribute on the view correctly."
            % (self.__class__.__name__, lookup_url_kwarg)
        )

        obj = next(
            (
                item
                for item in queryset
                if item[self.lookup_field] == self.kwargs[lookup_url_kwarg]
            ),
            None,
        )

        if obj is None:
            raise exceptions.NotFound()

        return obj

    def filter_queryset(self, queryset):
        filterset = super().filter_queryset(queryset)

        query_params = RepeatTradesViewSetFilterSerializer(
            data=self.request.query_params
        )
        query_params.is_valid(raise_exception=True)

        query = {
            key: value
            for key, value in query_params.validated_data.items()
            if key in self.request.query_params.keys()
        }

        filterset = filter_list_of_dictionaries(query, queryset)

        return filterset

    def get_queryset(self):
        query_params = RepeatTradesViewSetQueryParamsSerializer(
            context={"view": self, "request": self.request},
            data=self.request.query_params,
        )
        query_params.is_valid(raise_exception=True)
        query = query_params.validated_data

        self.trade_config_uuid = query.get("trade_config_uuid")

        node = self.get_node(trade_config_uuid=self.trade_config_uuid)

        api_response = self.tradecore_list_api(
            url=node.url,
            endpoint=self.tradecore_api_endpoint,
            query_params=query,
        )

        if api_response.status_code == HTTP_200_OK:
            return api_response.json()

        self.handle_exception_from_api(api_response)

    def perform_create(self, serializer):
        trade_config_allocation = self.get_trade_config_allocation(
            serializer.validated_data["trade_config_uuid"]
        )
        self.check_object_permissions(self.request, trade_config_allocation)
        serializer.save()

    def perform_destroy(self, instance):
        node = self.get_node(trade_config_uuid=self.trade_config_uuid)

        api_response = self.tradecore_destroy_api(
            url=node.url,
            endpoint=self.tradecore_api_endpoint,
            path_param=instance.get(self.lookup_field),
        )

        if api_response.status_code == HTTP_204_NO_CONTENT:
            return response.Response(status=HTTP_204_NO_CONTENT)

        self.handle_exception_from_api(api_response)


@extend_schema(tags=["ExchangeAPIKey"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List exchange api keys",
        description="Returns a list of all  `exchange api keys`.",
    ),
    create=extend_schema(
        operation_id="Create an exchange api key",
        description="Creates a new `exchange api key`.",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve an exchange api key",
        description="Retrieves the details of an existing `exchange api key`.",
    ),
    destroy=extend_schema(
        operation_id="Delete an exchange api key",
        description="Deletes an existing `exchange api key`.",
    ),
)
class ExchangeApiKeyViewSet(
    TradeCoreMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ExchangeApiKeyViewSetSerializer
    permission_classes = [IsAdmin | IsInternal | IsManager | IsUser]
    lookup_field = "uuid"
    tradecore_api_endpoint = "exchange-api-key/"
    http_method_names = ["get", "post", "delete"]

    def get_object(self):
        "Override get_object since our queryset is a dict and not a model"

        queryset = self.filter_queryset(self.get_queryset())

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            "Expected view %s to be called with a URL keyword argument "
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            "attribute on the view correctly."
            % (self.__class__.__name__, lookup_url_kwarg)
        )

        obj = next(
            (
                item
                for item in queryset
                if item[self.lookup_field] == self.kwargs[lookup_url_kwarg]
            ),
            None,
        )

        if obj is None:
            raise exceptions.NotFound()

        return obj

    # def filter_queryset(self, queryset):
    #     filterset = super().filter_queryset(queryset)

    #     query_params = TradesViewSetFilterSerializer(data=self.request.query_params)
    #     query_params.is_valid(raise_exception=True)

    #     query = {
    #         key: value
    #         for key, value in query_params.validated_data.items()
    #         if key in self.request.query_params.keys()
    #     }

    #     filterset = filter_list_of_dictionaries(query, queryset)

    #     return filterset

    def get_queryset(self):
        query_params = ExchangeApiKeyViewSetQueryParamsSerializer(
            context={"view": self, "request": self.request},
            data=self.request.query_params,
        )
        query_params.is_valid(raise_exception=True)
        query = query_params.validated_data

        node = self.get_node(trade_config_uuid=query.get("trade_config_uuid"))

        api_response = self.tradecore_list_api(
            url=node.url,
            endpoint=self.tradecore_api_endpoint,
            query_params=query,
        )

        if api_response.status_code == HTTP_200_OK:
            return api_response.json()

        self.handle_exception_from_api(api_response)

    def perform_create(self, serializer):
        trade_config_allocation = self.get_trade_config_allocation(
            serializer.validated_data["trade_config_uuid"]
        )
        self.check_object_permissions(self.request, trade_config_allocation)
        serializer.save()

    def perform_destroy(self, instance):
        node = self.get_node(trade_config_uuid=instance.get("trade_config_uuid"))

        api_response = self.tradecore_destroy_api(
            url=node.url,
            endpoint=self.tradecore_api_endpoint,
            path_param=instance.get(self.lookup_field),
        )

        if api_response.status_code == HTTP_204_NO_CONTENT:
            return response.Response(status=HTTP_204_NO_CONTENT)

        self.handle_exception_from_api(api_response)


@extend_schema_view(
    get=extend_schema(
        operation_id="Retrieve user capital",
        description="Retrieves the details of user's `capital`.",
        tags=["Capital"],
    ),
)
class CapitalView(TradeCoreMixin, views.APIView):
    http_method_names = ["get"]
    permission_classes = [IsAdmin | IsInternal | IsManager | IsUser]
    tradecore_api_endpoint = "capital/"

    def get(self, request):
        query_params = CapitalQueryParamsSerializer(
            context={"view": self, "request": request},
            data=request.query_params,
        )
        query_params.is_valid(raise_exception=True)
        query = query_params.validated_data

        self.trade_config_uuid = query.get("trade_config_uuid", "")
        self.market_code = query.get("market_code", "")

        data = self.get_cached_capital_data()
        if data is None:
            data = self.get_data()

        return response.Response(data)

    def get_data(self):
        trade_config_allocation = self.get_trade_config_allocation(
            trade_config_uuid=self.trade_config_uuid
        )
        node = trade_config_allocation.node

        query_params = {
            "market_code": self.market_code,
        }

        api_response = self.tradecore_retrieve_api(
            url=node.url,
            endpoint=self.tradecore_api_endpoint,
            path_param=trade_config_allocation.user.uuid,
            query_params=query_params,
        )

        if api_response.status_code == HTTP_200_OK:
            obj = api_response.json()
            self.check_object_permissions(self.request, obj)
            self.set_cached_capital_data(obj)
            return obj

        self.handle_exception_from_api(api_response)

    def get_cached_capital_data(self):
        return cache.get(self.get_redis_cache_key())

    def set_cached_capital_data(self, data):
        if data:
            cache.set(self.get_redis_cache_key(), data, timeout=5)

    def get_redis_cache_key(self):
        return f"acw:tradecore:capital:{self.trade_config_uuid}:{self.market_code}"


@extend_schema_view(
    get=extend_schema(
        operation_id="Retrieve user spot position",
        description="Retrieves the details of user's `spot position`.",
        tags=["SpotPosition"],
    ),
)
class SpotPositionView(TradeCoreMixin, views.APIView):
    http_method_names = ["get"]
    permission_classes = [IsAdmin | IsInternal | IsManager | IsUser]
    tradecore_api_endpoint = "spot-position/"

    def get(self, request):
        query_params = SpotPositionQueryParamsSerializer(
            context={"view": self, "request": request},
            data=request.query_params,
        )
        query_params.is_valid(raise_exception=True)
        query = query_params.validated_data

        self.trade_config_uuid = query.get("trade_config_uuid", "")
        self.market_code = query.get("market_code", "")
        self.user = query.get("user", request.user.uuid)

        data = self.get_cached_position_data()
        if data is None:
            data = self.get_data()

        return response.Response(data)

    def get_data(self):
        trade_config_allocation = self.get_trade_config_allocation(
            trade_config_uuid=self.trade_config_uuid
        )
        node = trade_config_allocation.node

        query_params = {
            "market_code": self.market_code,
        }

        api_response = self.tradecore_retrieve_api(
            url=node.url,
            endpoint=self.tradecore_api_endpoint,
            path_param=trade_config_allocation.user.uuid,
            query_params=query_params,
        )
        if api_response.status_code == HTTP_200_OK:
            obj = api_response.json()
            self.check_object_permissions(self.request, obj)
            self.set_cached_position_data(obj)
            return obj

        self.handle_exception_from_api(api_response)

    def get_cached_position_data(self):
        return cache.get(self.get_redis_cache_key())

    def set_cached_position_data(self, data):
        if data:
            cache.set(self.get_redis_cache_key(), data, timeout=10)

    def get_redis_cache_key(self):
        return f"acw:tradecore:spot-position:{self.trade_config_uuid}"


@extend_schema_view(
    get=extend_schema(
        operation_id="Retrieve user futures position",
        description="Retrieves the details of user's `futures position`.",
        tags=["FuturesPosition"],
    ),
)
class FuturesPositionView(TradeCoreMixin, views.APIView):
    http_method_names = ["get"]
    permission_classes = [IsAdmin | IsInternal | IsManager | IsUser]
    tradecore_api_endpoint = "futures-position/"

    def get(self, request):
        query_params = FuturePositionQueryParamsSerializer(
            context={"view": self, "request": request},
            data=request.query_params,
        )
        query_params.is_valid(raise_exception=True)
        query = query_params.validated_data

        self.trade_config_uuid = query.get("trade_config_uuid", "")
        self.market_code = query.get("market_code", "")
        self.user = query.get("user", request.user.uuid)

        data = self.get_cached_position_data()
        if data is None:
            data = self.get_data()

        return response.Response(data)

    def get_data(self):
        trade_config_allocation = self.get_trade_config_allocation(
            trade_config_uuid=self.trade_config_uuid
        )
        node = trade_config_allocation.node

        query_params = {
            "market_code": self.market_code,
        }

        api_response = self.tradecore_retrieve_api(
            url=node.url,
            endpoint=self.tradecore_api_endpoint,
            path_param=trade_config_allocation.user.uuid,
            query_params=query_params,
        )
        if api_response.status_code == HTTP_200_OK:
            obj = api_response.json()
            self.check_object_permissions(self.request, obj)
            self.set_cached_position_data(obj)
            return obj

        self.handle_exception_from_api(api_response)

    def get_cached_position_data(self):
        return cache.get(self.get_redis_cache_key())

    def set_cached_position_data(self, data):
        if data:
            cache.set(self.get_redis_cache_key(), data, timeout=10)

    def get_redis_cache_key(self):
        return f"acw:tradecore:futures-position:{self.trade_config_uuid}"


@extend_schema(tags=["OrderHistory"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List order history",
        description="Returns a list of all  `order history`.",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve a order history",
        description="Retrieves the details of an existing `order history`.",
    ),
)
class OrderHistoryViewSet(
    TradeCoreMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = OrderHistoryViewSetSerializer
    permission_classes = [IsAdmin | IsInternal | IsManager | IsUser]
    lookup_field = "order_id"
    tradecore_api_endpoint = "order-history/"
    http_method_names = ["get"]

    def get_object(self):
        "Override get_object since our queryset is a dict and not a model"

        queryset = self.filter_queryset(self.get_queryset())

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            "Expected view %s to be called with a URL keyword argument "
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            "attribute on the view correctly."
            % (self.__class__.__name__, lookup_url_kwarg)
        )

        obj = next(
            (
                item
                for item in queryset
                if item[self.lookup_field] == self.kwargs[lookup_url_kwarg]
            ),
            None,
        )

        if obj is None:
            raise exceptions.NotFound()

        return obj

    def get_queryset(self):
        query_params = OrderHistoryQueryParamsSerializer(
            context={"view": self, "request": self.request},
            data=self.request.query_params,
        )
        query_params.is_valid(raise_exception=True)
        query = query_params.validated_data

        node = self.get_node(trade_config_uuid=query.get("trade_config_uuid"))

        api_response = self.tradecore_list_api(
            url=node.url,
            endpoint=self.tradecore_api_endpoint,
            query_params=query,
        )

        if api_response.status_code == HTTP_200_OK:
            return api_response.json()

        self.handle_exception_from_api(api_response)


@extend_schema(tags=["TradeHistory"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List trade history",
        description="Returns a list of all  `trade history`.",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve a trade history",
        description="Retrieves the details of an existing `trade history`.",
    ),
)
class TradeHistoryViewSet(
    TradeCoreMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TradeHistoryViewSetSerializer
    permission_classes = [IsAdmin | IsInternal | IsManager | IsUser]
    lookup_field = "uuid"
    tradecore_api_endpoint = "trade-history/"
    http_method_names = ["get"]

    def get_object(self):
        "Override get_object since our queryset is a dict and not a model"

        queryset = self.filter_queryset(self.get_queryset())

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            "Expected view %s to be called with a URL keyword argument "
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            "attribute on the view correctly."
            % (self.__class__.__name__, lookup_url_kwarg)
        )

        obj = next(
            (
                item
                for item in queryset
                if item[self.lookup_field] == self.kwargs[lookup_url_kwarg]
            ),
            None,
        )

        if obj is None:
            raise exceptions.NotFound()

        return obj

    def filter_queryset(self, queryset):
        filterset = super().filter_queryset(queryset)

        query_params = TradeHistoryViewSetFilterSerializer(
            data=self.request.query_params
        )
        query_params.is_valid(raise_exception=True)

        query = {
            key: value
            for key, value in query_params.validated_data.items()
            if key in self.request.query_params.keys()
        }

        filterset = filter_list_of_dictionaries(query, queryset)

        return filterset

    def get_queryset(self):
        query_params = TradeHistoryQueryParamsSerializer(
            context={"view": self, "request": self.request},
            data=self.request.query_params,
        )
        query_params.is_valid(raise_exception=True)
        query = query_params.validated_data

        node = self.get_node(trade_config_uuid=query.get("trade_config_uuid"))

        api_response = self.tradecore_list_api(
            url=node.url,
            endpoint=self.tradecore_api_endpoint,
            query_params=query,
        )

        if api_response.status_code == HTTP_200_OK:
            return api_response.json()

        self.handle_exception_from_api(api_response)


@extend_schema(tags=["PNLHistory"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List PNL history",
        description="Returns a list of all  `PNL history`.",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve a PNL history",
        description="Retrieves the details of an existing `PNL history`.",
    ),
)
class PNLHistoryViewSet(
    TradeCoreMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = PNLHistoryViewSetSerializer
    permission_classes = [IsAdmin | IsInternal | IsManager | IsUser]
    lookup_field = "uuid"
    tradecore_api_endpoint = "pnl-history/"
    http_method_names = ["get"]

    def get_object(self):
        "Override get_object since our queryset is a dict and not a model"

        queryset = self.filter_queryset(self.get_queryset())

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            "Expected view %s to be called with a URL keyword argument "
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            "attribute on the view correctly."
            % (self.__class__.__name__, lookup_url_kwarg)
        )

        obj = next(
            (
                item
                for item in queryset
                if item[self.lookup_field] == self.kwargs[lookup_url_kwarg]
            ),
            None,
        )

        if obj is None:
            raise exceptions.NotFound()

        return obj

    def filter_queryset(self, queryset):
        filterset = super().filter_queryset(queryset)

        query_params = PNLHistoryViewSetFilterSerializer(data=self.request.query_params)
        query_params.is_valid(raise_exception=True)

        query = {
            key: value
            for key, value in query_params.validated_data.items()
            if key in self.request.query_params.keys()
        }

        filterset = filter_list_of_dictionaries(query, queryset)

        return filterset

    def get_queryset(self):
        query_params = PNLHistoryQueryParamsSerializer(
            context={"view": self, "request": self.request},
            data=self.request.query_params,
        )
        query_params.is_valid(raise_exception=True)
        query = query_params.validated_data

        node = self.get_node(trade_config_uuid=query.get("trade_config_uuid"))

        api_response = self.tradecore_list_api(
            url=node.url,
            endpoint=self.tradecore_api_endpoint,
            query_params=query,
        )

        if api_response.status_code == HTTP_200_OK:
            return api_response.json()

        self.handle_exception_from_api(api_response)


@extend_schema_view(
    get=extend_schema(
        operation_id="Get pboundary",
        description="Retrieves `pboundary` information.",
        tags=["Pboundary"],
    ),
)
class PboundaryView(TradeCoreMixin, views.APIView):
    http_method_names = ["get"]
    permission_classes = [IsAdmin | IsInternal | IsManager | IsUser]
    tradecore_api_endpoint = "pboundary/"

    def get(self, request):
        query_params = PboundaryQueryParamsSerializer(
            context={"view": self, "request": request},
            data=request.query_params,
        )
        query_params.is_valid(raise_exception=True)
        query = query_params.validated_data

        data = self.get_data(query)

        return response.Response(data)

    def get_data(self, query):
        trade_config_uuid = query.pop("trade_config_uuid", "")

        trade_config_allocation = self.get_trade_config_allocation(
            trade_config_uuid=trade_config_uuid
        )
        node = trade_config_allocation.node

        api_response = self.tradecore_list_api(
            url=node.url,
            endpoint=self.tradecore_api_endpoint,
            query_params=query,
        )

        if api_response.status_code == HTTP_200_OK:
            obj = api_response.json()
            return obj

        self.handle_exception_from_api(api_response)

@extend_schema_view(
    get=extend_schema(
        operation_id="Manually Exit a trade trigger for a user",
        description="Manually Exit a trade trigger for a user.",
        tags=["ExitTrade"],
    ),
)
class ExitTradeView(TradeCoreMixin, views.APIView):
    http_method_names = ["post"]
    permission_classes = [IsAdmin | IsInternal | IsManager | IsUser]
    tradecore_api_endpoint = "exit-trade/"

    def post(self, request):
        # Use request.data to get data from the POST body
        serializer = ExitTradeQueryParamsSerializer(
            context={"view": self, "request": request},
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        query = serializer.validated_data

        data = self.get_data(query)

        return response.Response(data)

    def get_data(self, query):
        trade_config_uuid = query.pop("trade_config_uuid", "")

        trade_config_allocation = self.get_trade_config_allocation(
            trade_config_uuid=trade_config_uuid
        )
        node = trade_config_allocation.node

        # Adjust the method to use 'post' and send data in the body
        api_response = self.tradecore_create_api(
            url=node.url,
            endpoint=self.tradecore_api_endpoint,
            data=query,
        )

        if api_response.status_code == HTTP_200_OK:
            obj = api_response.json()
            return obj

        self.handle_exception_from_api(api_response)

@extend_schema(tags=["TriggerScanner"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List trigger scanners",
        description="Returns a list of all `trigger scanners`.",
    ),
    create=extend_schema(
        operation_id="Create a trigger scanner",
        description="Creates a new `trigger scanner`.",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve a trigger scanner",
        description="Retrieves the details of an existing `trigger scanner`.",
    ),
    update=extend_schema(
        operation_id="Update a trigger scanner",
        description="Updates an existing `trigger scanner`.<br>"
        "*Only the parameters specified will be updated while the rest will be left unchanged.*",
    ),
    destroy=extend_schema(
        operation_id="Delete a trigger scanner",
        description="Deletes an existing `trigger scanner`.",
    ),
)
class TriggerScannerViewSet(
    TradeCoreMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TriggerScannerViewSetSerializer
    permission_classes = [IsAdmin | IsInternal | IsManager | IsUser]
    lookup_field = "uuid"
    tradecore_api_endpoint = "trigger-scanner/"
    http_method_names = ["get", "post", "put", "delete"]

    def get_object(self):
        "Override get_object since our queryset is a dict and not a model"
        trade_config_allocation = None
        try:
            for obj in self.get_queryset():
                if str(obj.get("uuid")) == self.kwargs[self.lookup_field]:
                    return obj
        except Exception:
            pass
        
        raise exceptions.NotFound()

    def filter_queryset(self, queryset):
        "Manual filter queryset using our filter class"
        query_serializer = TriggerScannerFilterSerializer(data=self.request.query_params)
        query_serializer.is_valid()
        query = query_serializer.validated_data

        if query:
            queryset = filter_list_of_dictionaries(query, queryset)

        return queryset

    def get_queryset(self):
        "Override get_queryset since we don't have model"
        query_serializer = TriggerScannerQueryParamsSerializer(
            data=self.request.query_params, context={"request": self.request}
        )
        query_serializer.is_valid(raise_exception=True)
        query = query_serializer.validated_data

        try:
            trade_config_allocation = self.get_trade_config_allocation(
                trade_config_uuid=query.get("trade_config_uuid"),
            )
            node = trade_config_allocation.node

            api_response = self.tradecore_list_api(
                url=node.url,
                endpoint=self.tradecore_api_endpoint,
                query_params={"trade_config_uuid": query.get("trade_config_uuid")},
            )

            if api_response.status_code == HTTP_200_OK:
                return api_response.json()

            self.handle_exception_from_api(api_response)

        except exceptions.APIException as err:
            raise err
        except Exception as err:
            raise exceptions.APIException({"detail": str(err)})

    def perform_create(self, serializer):
        self.check_object_permissions(self.request, dict(serializer.validated_data))
        serializer.save()

    def perform_destroy(self, instance):
        node = self.get_node(instance.get("trade_config_uuid"))

        api_response = self.tradecore_destroy_api(
            url=node.url,
            endpoint=self.tradecore_api_endpoint,
            path_param=instance.get("uuid"),
        )

        if api_response.status_code != HTTP_204_NO_CONTENT:
            self.handle_exception_from_api(api_response)