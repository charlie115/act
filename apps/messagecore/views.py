from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view

from lib.authentication import CoreIPAuthentication
from lib.views import BaseViewSet
from messagecore.models import Message
from messagecore.serializers import MessageSerializer


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
    queryset = Message.objects.all().order_by("id")
    serializer_class = MessageSerializer
    filter_backends = [DjangoFilterBackend]
    authentication_classes = [CoreIPAuthentication]
    permission_classes = []
    filterset_fields = (
        "origin",
        "type",
        "code",
        "telegram_chat_id",
        "telegram_bot_name",
        "sent",
    )
