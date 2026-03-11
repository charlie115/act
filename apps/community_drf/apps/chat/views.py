from django.conf import settings
from django.shortcuts import render
from drf_spectacular.utils import extend_schema, extend_schema_view
from pymongo import MongoClient
from pytz import timezone
from rest_framework import response, views
from rest_framework.pagination import PageNumberPagination

from chat.serializers import (
    PastChatMessagesSerializer,
    PastChatMessagesQueryParamsSerializer,
)
from lib.datetime import (
    TZ_ASIA_SEOUL,
    DATE_FORMAT_NUM,
    create_list_of_dates,
)
from lib.utils import get_client_ip, generate_username
from users.models import UserBlocklist


MONGODB_CLI = MongoClient(
    host=settings.MONGODB["HOST"],
    port=settings.MONGODB["PORT"],
    username=settings.MONGODB["USERNAME"],
    password=settings.MONGODB["PASSWORD"],
    appname="django-chat-api",
)


def chatbox(request):
    meta = request.META
    cookies = request.COOKIES
    client_ip = get_client_ip(request)

    email = (
        request.user.email if request.user and hasattr(request.user, "email") else ""
    )
    if "user" not in cookies:
        username = (
            request.user.username
            if request.user and hasattr(request.user, "username")
            else generate_username()
        )
    else:
        username = cookies["user"]

    context = {
        "meta": meta,
        "cookies": cookies,
        "ip": client_ip,
        "username": username,
        "email": email,
    }

    response = render(request, "chat/chat.html", context=context)
    if "user" not in cookies:
        response.set_cookie("user", username)

    return response


@extend_schema_view(
    get=extend_schema(
        operation_id="Get past chat messages",
        description="Returns past chat messages",
        parameters=[PastChatMessagesQueryParamsSerializer],
        responses={200: PastChatMessagesSerializer},
        tags=["PastChatMessages"],
    ),
)
class PastChatMessagesView(views.APIView, PageNumberPagination):
    http_method_names = ["get"]
    permission_classes = []
    page_size = 100

    def get(self, request):
        query_params = PastChatMessagesQueryParamsSerializer(data=request.query_params)
        query_params.is_valid(raise_exception=True)
        query = query_params.validated_data

        self.chat_db = MONGODB_CLI.get_database(settings.MONGO_CHAT_DB)

        data = self.get_chat_messages(
            start_time=query.get("start_time", None),
            end_time=query.get("end_time", None),
            tz=query.get("tz"),
        )

        return self.get_paginated_response(self.paginate_queryset(data, request))

    def get_chat_messages(self, start_time, end_time, tz):
        blocklist = UserBlocklist.objects.all()
        username_blocklist = [
            username
            for username in blocklist.values_list("target_username", flat=True)
            if bool(username)
        ]
        ip_blocklist = list(blocklist.values_list("target_ip", flat=True))

        if start_time and end_time:
            # Fix start_time and end_time to be inline with the user's tz first
            start_time = timezone(tz).localize(start_time.replace(tzinfo=None))
            end_time = timezone(tz).localize(end_time.replace(tzinfo=None))

            # Convert to KST since db collection is in KST (it's easier for devs to view the db)
            collections = create_list_of_dates(
                start_time.astimezone(TZ_ASIA_SEOUL),
                end_time.astimezone(TZ_ASIA_SEOUL),
                DATE_FORMAT_NUM,
            )
        else:
            collections = sorted(self.chat_db.list_collection_names())[-2:]

        # Prepare parameters
        query_filter = {
            "username": {"$nin": username_blocklist},
            "ip": {"$nin": ip_blocklist},
        }
        if start_time and end_time:
            query_filter["datetime"] = {
                "$gte": start_time,
                "$lte": end_time,
            }
        projection = {
            "_id": False,
        }

        all_results = []
        for collection in collections:
            # Query collection
            cursor = self.chat_db[collection].find(
                filter=query_filter,
                projection=projection,
            )

            # Serialize
            results = [
                PastChatMessagesSerializer(item, context={"tz": tz}).data
                for item in cursor
            ]
            all_results.extend(results)

        # Sort whole list
        all_results = sorted(
            all_results, key=lambda item: item["datetime"], reverse=True
        )

        return all_results


@extend_schema_view(
    get=extend_schema(
        operation_id="Get random username",
        description="Returns a random username",
        tags=["RandomUsername"],
    ),
)
class RandomUsernameView(views.APIView):
    http_method_names = ["get"]
    permission_classes = []

    def get(self, request):
        random_username = generate_username()

        return response.Response(random_username)
