from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination

from lib.views import BaseViewSet
from board.models import (
    Post,
    PostReactions,
    PostViews,
    Comment,
    CommentReactions,
)
from board.serializers import (
    PostSerializer,
    PostReactionsSerializer,
    PostViewsSerializer,
    CommentSerializer,
    CommentReactionsSerializer,
)


class CustomPageNumberPagination(PageNumberPagination):
    """
    Pagination doesn't work when using rest_framework.pagination.PageNumberPagination directly,
    nor using lib.pagination.CustomPageNumberPagination.
    I believe there's a bug with the order of the modules, so for now,
    we have to define our classes in the same module.
    """

    page_size = 50


@extend_schema(tags=["Comment"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List comments",
        description="Returns a list of all `comments`.",
    ),
    create=extend_schema(
        operation_id="Create a comment",
        description="Creates a new `comment`.",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve a comment",
        description="Retrieves the details of an existing `comment`.",
    ),
    update=extend_schema(
        operation_id="Fully update a comment",
        description="Fully updates an existing `comment`.<br>"
        "*All the previous values of the `comment` will be replaced with the new values provided. "
        "Any parameters not provided will be unset.*",
    ),
    partial_update=extend_schema(
        operation_id="Update a comment",
        description="Updates an existing `comment`.<br>"
        "*Only the parameters specified will be updated while the rest will be left unchanged.*",
    ),
    destroy=extend_schema(
        operation_id="Delete a comment",
        description="Deletes an existing `comment`.",
    ),
)
class CommentViewSet(BaseViewSet):
    queryset = Comment.objects.filter(
        parent__isnull=True
    )  # no need to return replies in main list
    lookup_field = "id"
    serializer_class = CommentSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = (
        "id",
        # "username",
        "date_created",
        "post",
        "parent",
    )
    ordering = [
        "-date_created",
    ]
    http_method_names = ["get", "post", "put", "patch", "delete"]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        return super(BaseViewSet, self).get_queryset()

    def get_permissions(self):
        permission_classes = self.permission_classes

        if self.action in ["list", "retrieve"]:
            permission_classes = []

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(tags=["Post"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List posts",
        description="Returns a list of all `posts`.",
    ),
    create=extend_schema(
        operation_id="Create a post",
        description="Creates a new `post`.",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve a post",
        description="Retrieves the details of an existing `post`.",
    ),
    update=extend_schema(
        operation_id="Fully update a post",
        description="Fully updates an existing `post`.<br>"
        "*All the previous values of the `post` will be replaced with the new values provided. "
        "Any parameters not provided will be unset.*",
    ),
    partial_update=extend_schema(
        operation_id="Update a post",
        description="Updates an existing `post`.<br>"
        "*Only the parameters specified will be updated while the rest will be left unchanged.*",
    ),
    destroy=extend_schema(
        operation_id="Delete a post",
        description="Deletes an existing `post`.",
    ),
)
class PostViewSet(BaseViewSet):
    queryset = Post.objects.all()
    lookup_field = "id"
    serializer_class = PostSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = (
        "id",
        # "username",
        "title",
        "date_created",
        "category",
        "content",
    )
    ordering = [
        "-date_created",
    ]
    http_method_names = ["get", "post", "put", "patch", "delete"]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        return super(BaseViewSet, self).get_queryset()

    def get_permissions(self):
        permission_classes = self.permission_classes

        if self.action in ["list", "retrieve"]:
            permission_classes = []

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(tags=["PostReactions"])
@extend_schema_view(
    create=extend_schema(
        operation_id="React to a post",
        description="Adds a new `post reaction` for a user.",
    ),
)
class PostReactionsViewSet(BaseViewSet):
    queryset = PostReactions.objects.all()
    lookup_field = "id"
    serializer_class = PostReactionsSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = (
        "id",
        # "username",
        "post",
        "date_updated",
    )
    ordering = [
        "id",
        "date_updated",
    ]
    http_method_names = ["post", "put", "patch", "delete"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(tags=["PostViews"])
@extend_schema_view(
    create=extend_schema(
        operation_id="View a post",
        description="Adds a new `post view` for a user.<br>"
        "View per post is counted only once per day for a user.",
    ),
)
class PostViewsViewSet(BaseViewSet):
    queryset = PostViews.objects.all()
    lookup_field = "id"
    serializer_class = PostViewsSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = (
        "id",
        # "username",
        "post",
        "date_viewed",
    )
    ordering = [
        "id",
        "date_viewed",
    ]
    http_method_names = ["post"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(tags=["CommentReactions"])
@extend_schema_view(
    create=extend_schema(
        operation_id="React to a comment",
        description="Adds a new `comment reaction` for a user.",
    ),
)
class CommentReactionsViewSet(BaseViewSet):
    queryset = CommentReactions.objects.all()
    lookup_field = "id"
    serializer_class = CommentReactionsSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = (
        "id",
        # "username",
        "comment",
        "date_updated",
    )
    ordering = [
        "id",
        "date_updated",
    ]
    http_method_names = ["post", "put", "patch", "delete"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
