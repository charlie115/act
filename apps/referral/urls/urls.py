from collections import OrderedDict
from django.urls import include, path
from rest_framework import response

from lib.views import BaseAPIListView
from referral.views import ReferralCommissionView


class ReferralAPIListView(BaseAPIListView):
    """
    Referral API endpoints
    """

    def get(self, request, *args, **kwargs):
        api_list = []

        for url in urlpatterns:
            endpoint = str(url.pattern)
            name = endpoint.strip("/")
            print(name, endpoint, request.build_absolute_uri(endpoint))

            if name != "":
                api_list.append(
                    (
                        name,
                        request.build_absolute_uri(endpoint),
                    )
                )

        api_list = OrderedDict(api_list)

        return response.Response(api_list)


app_name = "referral"

urlpatterns = [
    path("", ReferralAPIListView.as_view(), name="referral-root"),
    path(
        "referrals/",
        include("referral.urls.referrals"),
        name="referrals",
    ),
    path(
        "referral-code/",
        include("referral.urls.referral-code"),
        name="referral-code",
    ),
    path(
        "referral-commission/",
        ReferralCommissionView.as_view(),
        name="referral-commission-view",
    ),
]
