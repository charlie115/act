import os

from collections import OrderedDict
from django.urls import path
from rest_framework import response

from chat.views import PastChatMessagesView, RandomUsernameView, chatbox
from lib.views import BaseEndpointListView


class ChatAPIListView(BaseEndpointListView):
    """
    Chat API endpoints
    """

    def get(self, request, *args, **kwargs):
        api_list = []

        for url in urlpatterns:
            endpoint = str(url.pattern)
            name = endpoint.strip("/")
            if name != "":
                api_list.append(
                    (
                        name,
                        request.build_absolute_uri(endpoint),
                    )
                )

        api_list = OrderedDict(api_list)

        return response.Response(api_list)


urlpatterns = [
    path("", ChatAPIListView.as_view(), name="chat api list"),
    path("username/", RandomUsernameView.as_view(), name="random username"),
    path("past/", PastChatMessagesView.as_view(), name="past chat messages"),
]

if os.environ["DJANGO_SETTINGS_MODULE"] == "config.settings.dev":
    urlpatterns += [
        path("chatbox/", chatbox, name="chatbox"),
    ]
