from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination

from lib.authentication import NodeIPAuthentication
from lib.permissions import ACWBasePermission
from lib.views import BaseViewSet
from messagecore.models import Message
from messagecore.serializers import MessageSerializer
from users.models import UserRole


@extend_schema(tags=["Message"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List messages",
        description="Returns a list of all `messages` in messagecore.",
    ),
    create=extend_schema(
        operation_id="Create a message",
        description="Creates a new `message`.",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve a message",
        description="Retrieves the details of an existing `message`.",
    ),
    update=extend_schema(
        operation_id="Fully update a message",
        description="Fully updates an existing `message`.<br>"
        "*All the previous values of the `message` will be replaced with the new values provided. "
        "Any parameters not provided will be unset.*",
    ),
    partial_update=extend_schema(
        operation_id="Update a message",
        description="Updates an existing `message`.<br>"
        "*Only the parameters specified will be updated while the rest will be left unchanged.*",
    ),
    destroy=extend_schema(
        operation_id="Delete a message",
        description="Deletes an existing `message`.",
    ),
)
class MessageViewSet(BaseViewSet):
    queryset = Message.objects.exclude(type=Message.MONITOR)
    serializer_class = MessageSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = (
        "origin",
        "type",
        "code",
        "telegram_chat_id",
        "telegram_bot_username",
        "sent",
    )
    ordering_fields = ["id"]
    ordering = ["-datetime"]
    http_method_names = ["get", "post", "put", "patch", "delete"]
    pagination_class = PageNumberPagination
    pagination_class.page_size = 50

    def get_queryset(self):
        """Override BaseViewSet get_queryset since Message table has no relationship to User
        but can still be associated through telegram_chat_id"""

        queryset = super(MessageViewSet, self).get_queryset()

        query_field = ""
        query = {}

        if self.request.user:
            query_field = "telegram_chat_id__in"
            query = {query_field: [self.request.user.telegram_chat_id]}

            if self.request.user.role.name == UserRole.ADMIN:
                return queryset

            if (
                self.request.user.role.name == UserRole.INTERNAL_USER
                and ACWBasePermission().has_api_permission(self.request)
            ):
                return queryset

            if (
                self.request.user.role.name == UserRole.MANAGER
                and ACWBasePermission().has_api_permission(self.request)
            ):
                managed_user_telegram_chat_ids = (
                    self.request.user.managed_users.values_list(
                        "managed_user__telegram_chat_id",
                        flat=True,
                    )
                )

                try:
                    query[query_field] += managed_user_telegram_chat_ids
                except KeyError:
                    pass

        return queryset.filter(**query)

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
