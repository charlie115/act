from django.db import connections
from drf_spectacular.utils import extend_schema, extend_schema_view

from arbot.models import ArbotNode, ArbotUserConfig, get_historical_coin_data_model
from arbot.serializers import (
    ArbotNodeSerializer,
    ArbotUserConfigSerializer,
    ArbotHistoricalCoinDataQueryParamsSerializer,
    ArbotHistoricalCoinDataSerializer,
)
from lib.views import BaseViewSet, UserOwned1To1ViewSet

from rest_framework import exceptions, generics


@extend_schema(tags=["ArbotNode"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List arbot nodes",
        description="Returns a list of all arbot `nodes`.",
    ),
    create=extend_schema(
        operation_id="Create an arbot node",
        description="Creates a new arbot `node`.",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve an arbot node",
        description="Retrieves the details of an existing arbot `node`.",
    ),
    update=extend_schema(
        operation_id="Fully update an arbot node",
        description="Fully updates an existing arbot `node`.<br>"
        "*All the previous values of the arbot `node` will be replaced with the new values provided. "
        "Any parameters not provided will be unset.*",
    ),
    partial_update=extend_schema(
        operation_id="Update an arbot node",
        description="Updates an existing arbot ` node`.<br>"
        "*Only the parameters specified will be updated while the rest will be left unchanged.*",
    ),
    destroy=extend_schema(
        operation_id="Delete an arbot node",
        description="Deletes an existing arbot `node`.",
    ),
)
class ArbotNodeViewSet(BaseViewSet):
    queryset = ArbotNode.objects.all().order_by("id")
    serializer_class = ArbotNodeSerializer


@extend_schema(tags=["ArbotUserConfig"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List arbot user configurations",
        description="Returns a list of all arbot `user configurations`.",
    ),
    create=extend_schema(
        operation_id="Create an arbot user configuration",
        description="Creates a new arbot `user configuration`.",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve an arbot user configuration",
        description="Retrieves the details of an existing arbot `user configuration`.",
    ),
    update=extend_schema(
        operation_id="Fully update an arbot user configuration",
        description="Fully updates an existing arbot `user configuration`.<br>"
        "*All the previous values of the arbot `user configuration` will be replaced with the new values provided. "
        "Any parameters not provided will be unset.*",
    ),
    partial_update=extend_schema(
        operation_id="Update an arbot user configuration",
        description="Updates an existing arbot `user configuration`.<br>"
        "*Only the parameters specified will be updated while the rest will be left unchanged.*",
    ),
    destroy=extend_schema(
        operation_id="Delete an arbot user configuration",
        description="Deletes an existing arbot `user configuration`.",
    ),
)
class ArbotUserConfigViewSet(UserOwned1To1ViewSet):
    queryset = ArbotUserConfig.objects.all().order_by("id")
    serializer_class = ArbotUserConfigSerializer


@extend_schema(operation_id="Arbot historical coin price data")
class ArbotHistoricalCoinDataView(generics.ListAPIView):
    serializer_class = ArbotHistoricalCoinDataSerializer

    def get_queryset(self):
        query_params = ArbotHistoricalCoinDataQueryParamsSerializer(
            data=self.request.query_params
        )
        query_params.is_valid(raise_exception=True)
        query = query_params.validated_data

        table_name = f"{query['exchange_market_1']}:{query['exchange_market_2']}_{query['period']}_kline"

        self.check_if_table_exists(table_name)

        model = get_historical_coin_data_model(table_name)
        model._meta.db_table = table_name

        return model.objects.all()

    @staticmethod
    def check_if_table_exists(table_name):
        conn = connections["info_core"]
        tables = conn.introspection.table_names(conn.cursor())

        if table_name not in tables:
            raise exceptions.ValidationError({"detail": "Bad request."})
