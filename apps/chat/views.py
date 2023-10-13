from datetime import datetime
from django.conf import settings
from django.shortcuts import render
from drf_spectacular.utils import extend_schema, extend_schema_view
from pymongo import MongoClient, DESCENDING
from pytz import timezone
from rest_framework import response, views

from chat.serializers import (
    PastChatMessagesSerializer,
    PastChatMessagesQueryParamsSerializer,
)
from lib.datetime import (
    ASIA_SEOUL_TZ,
    DATE_FORMAT_NUM,
    DATE_TIME_FORMAT,
    create_list_of_dates,
)
from lib.utils import get_client_ip, generate_username
from users.models import UserBlocklist


MONGODB_CLI = MongoClient(
    host=settings.MONGODB["HOST"],
    port=settings.MONGODB["PORT"],
    username=settings.MONGODB["USERNAME"],
    password=settings.MONGODB["PASSWORD"],
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
class PastChatMessagesView(views.APIView):
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
        )

        return response.Response(data)

    def get_chat_messages(self, start_time, end_time):
        blocklist = UserBlocklist.objects.all()
        email_blocklist = list(blocklist.values_list("target_email", flat=True))
        ip_blocklist = list(blocklist.values_list("target_ip", flat=True))

        now_kst = datetime.now(tz=timezone(ASIA_SEOUL_TZ))
        start_time = start_time.strftime(DATE_TIME_FORMAT) if start_time else start_time
        end_time = end_time.strftime(DATE_TIME_FORMAT) if end_time else end_time

        collections = (
            create_list_of_dates(start_time, end_time, DATE_FORMAT_NUM)
            if start_time and end_time
            else [now_kst.strftime(DATE_FORMAT_NUM)]
        )

        all_results = []
        for collection in collections:
            coll = self.chat_db.get_collection(collection)

            # Prepare parameters
            query_filter = {
                "email": {"$nin": email_blocklist},
                "username": {"$nin": ip_blocklist},
            }
            if start_time and end_time:
                query_filter["datetime"] = {
                    "$gte": start_time,
                    "$lte": end_time,
                }
            projection = {
                "_id": False,
            }

            # Query collection
            cursor = coll.find(
                filter=query_filter,
                projection=projection,
            )

            # If no start_time and end_time, get latest n data
            if not (start_time and end_time):
                cursor = cursor.sort("datetime_now", DESCENDING).limit(self.page_size)

            # Sort back for display
            results = [
                {key: value for key, value in item.items() if key != "ip"}
                for item in cursor
            ]
            all_results.extend(results)

        all_results = sorted(all_results, key=lambda item: item["datetime"])

        return all_results
