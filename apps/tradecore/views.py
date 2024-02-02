from django_filters import CharFilter, FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import exceptions, mixins, response, viewsets
from rest_framework.decorators import action

from lib.views import BaseViewSet
from lib.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND
from tradecore.mixins import TradeCoreMixin
from tradecore.models import Node
from tradecore.serializers import (
    NodeSerializer,
    TradeConfigViewSetSerializer,
    TradesViewSetQueryParamsSerializer,
    TradesViewSetFilterSerializer,
    TradesViewSetSerializer,
)


class NodeFilter(FilterSet):
    description__contains = CharFilter(field_name="description", lookup_expr="contains")

    class Meta:
        model = Node
        fields = ("name", "url", "description", "max_user_count")


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
    queryset = Node.objects.all().order_by("id")
    serializer_class = NodeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = NodeFilter


###################
# Trade Core APIs #
###################


@extend_schema_view(
    list=extend_schema(
        operation_id="List exchange configs",
        description="Returns a list of all  `exchange configs`.",
        tags=["ExchangeConfig"],
    ),
    create=extend_schema(
        operation_id="Create an exchange config",
        description="Creates a new `exchange config`.",
        tags=["ExchangeConfig"],
    ),
    retrieve=extend_schema(
        operation_id="Retrieve an exchange config",
        description="Retrieves the details of an existing `exchange config`.",
        tags=["ExchangeConfig"],
    ),
    update=extend_schema(
        operation_id="Fully update an exchange config",
        description="Fully updates an existing `exchange config`.<br>"
        "*All the previous values of the `exchange config` will be replaced with the new values provided. "
        "Any parameters not provided will be unset.*",
        tags=["ExchangeConfig"],
    ),
    destroy=extend_schema(
        operation_id="Delete an exchange config",
        description="Deletes an existing `exchange config`.",
        tags=["ExchangeConfig"],
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
    lookup_field = "uuid"
    tradecore_api_endpoint = "trade-config/"

    def get_object(self):
        trade_config_allocation = self.get_trade_config_allocation(
            trade_config_uuid=self.kwargs[self.lookup_field]
        )
        node = trade_config_allocation.node

        api_response = self.tradecore_retrieve_api(
            url=node.url,
            endpoint=self.tradecore_api_endpoint,
            path_param=trade_config_allocation.trade_config_uuid,
        )
        if api_response.status_code == HTTP_200_OK:
            return api_response.json()

        self.handle_exception_from_api(api_response)

    def perform_destroy(self, instance):
        trade_config_allocation = self.get_trade_config_allocation(
            trade_config_uuid=instance.get(self.lookup_field)
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
    # delete=extend_schema(
    #     operation_id="Delete all user trades",
    #     description="Deletes all `trades` of a user.",
    # ),
)
class TradesViewSet(
    TradeCoreMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = TradesViewSetSerializer
    lookup_field = "uuid"
    tradecore_api_endpoint = "trades/"

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
        query = query_params.validated_data.copy()

        filterset = filter(
            lambda item: all((item[k] == v for (k, v) in query.items())),
            queryset,
        )

        return filterset

    def get_queryset(self):
        query_params = TradesViewSetQueryParamsSerializer(
            data=self.request.query_params
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
    def delete(self, request):
        query_params = TradesViewSetQueryParamsSerializer(
            data=self.request.query_params
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
