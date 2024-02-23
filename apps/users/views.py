from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view

from lib.filters import CharArrayFilter, UserUuidFilter
from lib.views import BaseViewSet
from users.models import (
    User,
    UserBlocklist,
    UserFavoriteAssets,
    UserProfile,
)
from users.serializers import (
    UserSerializer,
    UserFavoriteAssetsSerializer,
    UserProfileSerializer,
    UserBlocklistSerializer,
)


###########
# Filters #
###########
class UserFavoriteAssetsFilter(UserUuidFilter):
    market_codes = CharArrayFilter(field_name="market_codes", lookup_expr="contains")

    class Meta:
        model = UserFavoriteAssets
        fields = ("user", "base_asset", "market_codes")


class UserProfileFilter(UserUuidFilter):
    class Meta:
        model = UserProfile
        fields = ("user", "referral", "level", "points")


#########
# Views #
#########
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
    queryset = User.objects.all().order_by("id")
    lookup_field = "uuid"
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend]
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
class UserFavoriteAssetsViewSet(BaseViewSet):
    queryset = UserFavoriteAssets.objects.all().order_by("id")
    serializer_class = UserFavoriteAssetsSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserFavoriteAssetsFilter
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
class UserProfileViewSet(BaseViewSet):
    queryset = UserProfile.objects.all().order_by("id")
    serializer_class = UserProfileSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserProfileFilter
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
    queryset = UserBlocklist.objects.all().order_by("id")
    serializer_class = UserBlocklistSerializer
    filter_backends = [DjangoFilterBackend]
    http_method_names = ["get", "post", "delete"]
