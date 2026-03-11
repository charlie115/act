from collections import OrderedDict
from django.urls import include, path
from rest_framework import response

from lib.views import BaseAPIListView
from referral.views import (
    ReferralCommissionView,
    CommissionHistoryListView,
    CommissionBalanceListView,
    SubAffiliateListView,
)

class ReferralAPIListView(BaseAPIListView):
    """
    Referral API endpoints
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
    path(
        "affiliate-request/",
        include("referral.urls.affiliate-request"),
        name="affiliate-request",
    ),
    path(
        "affiliate/",
        include("referral.urls.affiliate"),
        name="affiliate",
    ),
    path(
        "sub-affiliate/",
        SubAffiliateListView.as_view(),
        name="sub-affiliate",
    ),
    path(
        "affiliate-tier/",
        include("referral.urls.affiliate-tier"),
        name="affiliate-tier",
    ),
    path(
        "commission-history/",
        CommissionHistoryListView.as_view(),
        name="commission-history",
    ),
    path(
        "commission-balance/",
        CommissionBalanceListView.as_view(),
        name="commission-balance",
    ),
]
