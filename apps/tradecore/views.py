from django_filters import CharFilter, FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view

from tradecore.models import Node, UserConfig
from tradecore.serializers import NodeSerializer, UserConfigSerializer
from lib.filters import UserUuidFilter
from lib.views import BaseViewSet, UserOwned1To1ViewSet


class NodeFilter(FilterSet):
    description__contains = CharFilter(field_name="description", lookup_expr="contains")

    class Meta:
        model = Node
        fields = "__all__"


class UserConfigFilter(UserUuidFilter):
    class Meta:
        model = UserConfig
        fields = "__all__"


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


@extend_schema(tags=["UserConfig"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List user configurations",
        description="Returns a list of all `user configurations`.",
    ),
    create=extend_schema(
        operation_id="Create a user configuration",
        description="Creates a new `user configuration`.",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve a user configuration",
        description="Retrieves the details of an existing `user configuration`.",
    ),
    update=extend_schema(
        operation_id="Fully update a user configuration",
        description="Fully updates an existing `user configuration`.<br>"
        "*All the previous values of the `user configuration` will be replaced with the new values provided. "
        "Any parameters not provided will be unset.*",
    ),
    partial_update=extend_schema(
        operation_id="Update a user configuration",
        description="Updates an existing `user configuration`.<br>"
        "*Only the parameters specified will be updated while the rest will be left unchanged.*",
    ),
    destroy=extend_schema(
        operation_id="Delete an user configuration",
        description="Deletes an existing `user configuration`.",
    ),
)
class UserConfigViewSet(UserOwned1To1ViewSet):
    queryset = UserConfig.objects.all().order_by("id")
    serializer_class = UserConfigSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserConfigFilter
