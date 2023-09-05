from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from users.models import User, UserFavoriteSymbols, UserProfile
from users.serializers import (
    UserSerializer,
    UserFavoriteSymbolsSerializer,
    UserProfileSerializer,
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
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer


@extend_schema(tags=["UserFavoriteSymbol"])
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
class UserFavoriteSymbolsViewSet(viewsets.ModelViewSet):
    queryset = UserFavoriteSymbols.objects.all().order_by("id")
    serializer_class = UserFavoriteSymbolsSerializer
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
class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all().order_by("id")
    serializer_class = UserProfileSerializer
    http_method_names = ["get", "put", "patch", "delete"]
