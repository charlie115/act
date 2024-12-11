from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.filters import OrderingFilter

from lib.authentication import NodeIPAuthentication
from lib.views import BaseViewSet, UserOwnedViewSet
from users.filters import (
    UserFavoriteAssetsFilter,
    UserProfileFilter,
    DepositBalanceFilter,
    DepositHistoryFilter,
)
from users.models import (
    User,
    UserBlocklist,
    UserFavoriteAssets,
    UserProfile,
    DepositBalance,
    DepositHistory,
    WithdrawalRequest,
)
from users.serializers import (
    UserSerializer,
    UserFavoriteAssetsSerializer,
    UserProfileSerializer,
    UserBlocklistSerializer,
    DepositBalanceSerializer,
    DepositHistorySerializer,
    WithdrawalRequestSerializer,
)


@extend_schema(tags=["User"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List users",
        description="Returns a list of all `users`.",
    ),
    create=extend_schema(
        operation_id="Create a user",
        description="Creates a new `user`.",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve a user",
        description="Retrieves the details of an existing `user`.",
    ),
    update=extend_schema(
        operation_id="Fully update a user",
        description="Fully updates an existing `user`.<br>"
        "*All the previous values of the `user` will be replaced with the new values provided. "
        "Any parameters not provided will be unset.*",
    ),
    partial_update=extend_schema(
        operation_id="Update a user",
        description="Updates an existing `user`.<br>"
        "*Only the parameters specified will be updated while the rest will be left unchanged.*",
    ),
    destroy=extend_schema(
        operation_id="Delete a user",
        description="Deletes an existing `user`.",
    ),
)
class UserViewSet(BaseViewSet):
    queryset = User.objects.all()
    lookup_field = "uuid"
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = (
        "email",
        "uuid",
        "username",
        "first_name",
        "last_name",
        "telegram_chat_id",
        "role",
        "is_active",
    )
    ordering_fields = [
        "id",
        "email",
        "username",
        "first_name",
        "last_name",
        "telegram_chat_id",
    ]
    ordering = ["email"]
    http_method_names = ["get", "post", "put", "patch", "delete"]


@extend_schema(tags=["UserFavoriteAssets"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List user favorite symbols",
        description="Returns a list of all user `favorite symbols`.",
    ),
    create=extend_schema(
        operation_id="Add a new user favorite symbol",
        description="Adds a new user `favorite symbol`.",
    ),
    retrieve=extend_schema(exclude=True),
    update=extend_schema(exclude=True),
    partial_update=extend_schema(exclude=True),
    destroy=extend_schema(
        operation_id="Delete a user favorite symbol",
        description="Deletes an existing user `favorite symbol`.",
    ),
)
class UserFavoriteAssetsViewSet(UserOwnedViewSet):
    queryset = UserFavoriteAssets.objects.all()
    serializer_class = UserFavoriteAssetsSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = UserFavoriteAssetsFilter
    ordering_fields = [
        "id",
        "base_asset",
        "user",
    ]
    ordering = ["id"]
    http_method_names = ["get", "post", "delete"]


@extend_schema(tags=["UserProfile"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List user profiles",
        description="Returns a list of all user `profiles`.",
    ),
    create=extend_schema(exclude=True),
    retrieve=extend_schema(
        operation_id="Retrieve a user profile",
        description="Retrieves the details of an existing user `profile`.",
    ),
    update=extend_schema(
        operation_id="Fully update a user profile",
        description="Fully updates an existing user `profile`.<br>"
        "*All the previous values of the user `profile` will be replaced with the new values provided. "
        "Any parameters not provided will be unset.*",
    ),
    partial_update=extend_schema(
        operation_id="Update a user profile",
        description="Updates an existing user `profile`.<br>"
        "*Only the parameters specified will be updated while the rest will be left unchanged.*",
    ),
    destroy=extend_schema(exclude=True),
)
class UserProfileViewSet(UserOwnedViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = UserProfileFilter
    ordering_fields = [
        "id",
        "user",
        "level",
        "points",
    ]
    ordering = ["id"]
    http_method_names = ["get", "put", "patch", "delete"]


@extend_schema(tags=["UserBlocklist"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List blocked users",
        description="Returns a list of all blocked users.",
    ),
    create=extend_schema(
        operation_id="Add a new user to block",
        description="Adds a new user to block.",
    ),
    retrieve=extend_schema(exclude=True),
    update=extend_schema(exclude=True),
    partial_update=extend_schema(exclude=True),
    destroy=extend_schema(
        operation_id="Delete a blocked user",
        description="Deletes a blocked user.",
    ),
)
class UserBlocklistViewSet(BaseViewSet):
    queryset = UserBlocklist.objects.all()
    serializer_class = UserBlocklistSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = [
        "id",
        "target_username",
        "target_ip",
        "datetime",
    ]
    ordering = ["id"]
    http_method_names = ["get", "post", "delete"]


@extend_schema(tags=["DepositBalance"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List deposit balance",
        description="Returns a list of all `deposit balance`.",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve a deposit balance",
        description="Retrieves the details of an existing `deposit balance`.",
    ),
)
class DepositBalanceViewSet(UserOwnedViewSet):
    queryset = DepositBalance.objects.all()
    lookup_field = "id"
    serializer_class = DepositBalanceSerializer
    filterset_class = DepositBalanceFilter
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = [
        "id",
        "user",
        "balance",
        "last_update",
    ]
    ordering = ["id"]
    http_method_names = ["get"]

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


@extend_schema(tags=["DepositHistory"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List deposit history",
        description="Returns a list of all `deposit history`.",
    ),
    create=extend_schema(
        operation_id="Create a deposit history",
        description="Creates a new `deposit history`.",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve a deposit history",
        description="Retrieves the details of an existing `deposit history`.",
    ),
    update=extend_schema(
        operation_id="Fully update a deposit history",
        description="Fully updates an existing `deposit history`.<br>"
        "*All the previous values of the `deposit history` will be replaced with the new values provided. "
        "Any parameters not provided will be unset.*",
    ),
    partial_update=extend_schema(
        operation_id="Update a deposit history",
        description="Updates an existing `deposit history`.<br>"
        "*Only the parameters specified will be updated while the rest will be left unchanged.*",
    ),
    destroy=extend_schema(
        operation_id="Delete a deposit history",
        description="Deletes an existing `deposit history`.",
    ),
)
class DepositHistoryViewSet(UserOwnedViewSet):
    queryset = DepositHistory.objects.all()
    lookup_field = "id"
    serializer_class = DepositHistorySerializer
    filterset_class = DepositHistoryFilter
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = [
        "id",
        "user",
        "balance",
        "change",
        "registered_datetime",
    ]
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
    
@extend_schema(tags=["WithdrawalRequest"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List withdrawal requests",
        description="Returns a list of all `withdrawal requests`.",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve a withdrawal request",
        description="Retrieves the details of an existing `withdrawal requests`.",
    ),
    create=extend_schema(
        operation_id="Create a withdrawal request",
        description="Creates a new `withdrawal request`.",
    ),
)
class WithdrawalRequestViewSet(UserOwnedViewSet):
    queryset = WithdrawalRequest.objects.all()
    serializer_class = WithdrawalRequestSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['user', 'type', 'status', 'type']
    ordering_fields = ['id', 'user', 'amount', 'type', 'status', 'requested_datetime', 'approved_datetime', 'completed_datetime',]
    ordering = ['id']
    http_method_names = ['get', 'post']
    