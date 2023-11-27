from django.urls import path

from infocore.views import (
    FundingRateDataView,
    FundingRateDiffDataView,
)


urlpatterns = [
    path(
        "",
        FundingRateDataView.as_view(),
        name="funding rate data",
    ),
    path(
        "diff/",
        FundingRateDiffDataView.as_view(),
        name="funding rate diff data",
    ),
]
