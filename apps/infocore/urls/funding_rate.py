from django.urls import path

from infocore.views import (
    FundingRateDataView,
)


urlpatterns = [
    path(
        "",
        FundingRateDataView.as_view(),
        name="funding rate data",
    ),
]
