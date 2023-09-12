from drf_spectacular.utils import extend_schema, extend_schema_view

from arbot.models import ArbotNode, ArbotUserConfig
from arbot.serializers import ArbotNodeSerializer, ArbotUserConfigSerializer
from lib.views import BaseViewSet


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
class ArbotUserConfigViewSet(BaseViewSet):
    queryset = ArbotUserConfig.objects.all().order_by("id")
    serializer_class = ArbotUserConfigSerializer
