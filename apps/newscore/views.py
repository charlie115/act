from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view

from lib.pagination import CustomPageNumberPagination
from lib.views import BaseViewSet
from newscore.models import Announcement, News
from newscore.serializers import AnnouncementSerializer, NewsSerializer


@extend_schema(tags=["News"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List news articles",
        description="Returns a list of news articles",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve a news article",
        description="Retrieve details of an existing news article.",
    ),
)
class NewsViewSet(BaseViewSet):
    queryset = News.objects.all().order_by("-datetime")
    serializer_class = NewsSerializer
    filter_backends = [DjangoFilterBackend]
    http_method_names = ["get"]
    permission_classes = []
    pagination_class = CustomPageNumberPagination
    pagination_class.page_size = 10


@extend_schema(tags=["Announcements"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List announcements",
        description="Returns a list of announcements",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve announcement",
        description="Retrieve details of an existing announcement.",
    ),
)
class AnnouncementViewSet(BaseViewSet):
    queryset = Announcement.objects.all().order_by("-datetime")
    serializer_class = AnnouncementSerializer
    filter_backends = [DjangoFilterBackend]
    http_method_names = ["get"]
    permission_classes = []
    pagination_class = CustomPageNumberPagination
    pagination_class.page_size = 10
