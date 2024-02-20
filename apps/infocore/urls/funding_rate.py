from django.urls import path

from infocore.views import (
    AverageFundingRateDataView,
    FundingRateDataView,
    FundingRateDiffDataView,
)

app_name = "infocore:funding-rate"


urlpatterns = [
    path(
        "",
        FundingRateDataView.as_view(),
        name="funding-rate-view",
    ),
    path(
        "average/",
        AverageFundingRateDataView.as_view(),
        name="average-funding-rate-view",
    ),
    path(
        "diff/",
        FundingRateDiffDataView.as_view(),
        name="funding-rate-diff-view",
    ),
]
