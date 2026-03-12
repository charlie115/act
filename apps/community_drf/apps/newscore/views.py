from django_filters import FilterSet, ChoiceFilter, DateTimeFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from pytz import all_timezones, timezone
from rest_framework.filters import OrderingFilter
from django.db import OperationalError, ProgrammingError

from lib.datetime import TZ_UTC
from lib.pagination import CustomPageNumberPagination
from lib.views import BaseViewSet
from newscore.models import Announcement, News, Post
from newscore.serializers import AnnouncementSerializer, NewsSerializer, PostSerializer


class SafeManagedFalseQuerysetMixin:
    model = None

    def get_queryset(self):
        queryset = super().get_queryset()
        try:
            queryset.exists()
            return queryset
        except (ProgrammingError, OperationalError):
            if self.model is None:
                return queryset.none()
            return self.model.objects.none()


class StartTimeEndTimeFilter(FilterSet):
    start_time = DateTimeFilter(field_name="datetime", lookup_expr="gte")
    end_time = DateTimeFilter(field_name="datetime", lookup_expr="lte")
    tz = ChoiceFilter(
        choices=[(tz, tz) for tz in all_timezones],
        method="get_tz",
    )

    def get_tz(self, queryset, name, value):
        return queryset

    def filter_queryset(self, queryset):
        tz = self.form.cleaned_data.pop("tz")
        tz = timezone(tz) if tz else TZ_UTC

        for name, value in self.form.cleaned_data.items():
            if name in ["start_time", "end_time"] and value:
                value = tz.localize(value.replace(tzinfo=None))
            queryset = self.filters[name].filter(queryset, value)
        return queryset


class AnnouncementFilter(StartTimeEndTimeFilter):
    class Meta:
        model = Announcement
        fields = ("category", "exchange", "start_time", "end_time", "tz")


class NewsFilter(StartTimeEndTimeFilter):
    class Meta:
        model = News
        fields = ("media", "start_time", "end_time", "tz")


class PostFilter(StartTimeEndTimeFilter):
    class Meta:
        model = Post
        fields = ("name", "username", "social_media", "start_time", "end_time", "tz")


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
class NewsViewSet(SafeManagedFalseQuerysetMixin, BaseViewSet):
    model = News
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = NewsFilter
    ordering_fields = ["id"]
    ordering = ["-datetime"]
    permission_classes = []
    pagination_class = CustomPageNumberPagination
    pagination_class.page_size = 10
    http_method_names = ["get"]


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
class AnnouncementViewSet(SafeManagedFalseQuerysetMixin, BaseViewSet):
    model = Announcement
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = AnnouncementFilter
    ordering_fields = ["id"]
    ordering = ["-datetime"]
    permission_classes = []
    pagination_class = CustomPageNumberPagination
    pagination_class.page_size = 10
    http_method_names = ["get"]


@extend_schema(tags=["SNS Posts"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List sns posts",
        description="Returns a list of sns posts",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve post",
        description="Retrieve details of an existing sns post.",
    ),
)
class PostViewSet(SafeManagedFalseQuerysetMixin, BaseViewSet):
    model = Post
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = PostFilter
    ordering_fields = ["id"]
    ordering = ["-datetime"]
    permission_classes = []
    pagination_class = CustomPageNumberPagination
    pagination_class.page_size = 10
    http_method_names = ["get"]
