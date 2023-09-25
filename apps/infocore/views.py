import pymongo
from django.conf import settings
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import exceptions, views
from rest_framework.pagination import PageNumberPagination


from infocore.serializers import (
    InfoCoreHistoricalCoinDataSerializer,
    InfoCoreHistoricalCoinDataQueryParamsSerializer,
)


mongodb = pymongo.MongoClient(settings.MONGODB["HOST"], settings.MONGODB["PORT"])


@extend_schema_view(
    get=extend_schema(
        operation_id="Get historical coin price data",
        description="Returns a list of historical coin price data.",
        parameters=[InfoCoreHistoricalCoinDataQueryParamsSerializer],
        responses={200: InfoCoreHistoricalCoinDataSerializer},
        tags=["Coin"],
    ),
)
class InfoCoreHistoricalCoinDataView(views.APIView, PageNumberPagination):
    PageNumberPagination.page_size = 200

    def get(self, request):
        query_params = InfoCoreHistoricalCoinDataQueryParamsSerializer(
            data=request.query_params
        )
        query_params.is_valid(raise_exception=True)
        query = query_params.validated_data

        data = self.get_data(
            exchange_market_1=query["exchange_market_1"],
            exchange_market_2=query["exchange_market_2"],
            period=query["period"],
            coin=query["coin"],
        )

        return self.get_paginated_response(self.paginate_queryset(data, request))

    def get_data(self, exchange_market_1, exchange_market_2, period, coin):
        db_name = f"{exchange_market_1}-{exchange_market_2}"
        collection_name = f"{coin}_{period}"

        dbs = mongodb.list_database_names()
        if db_name not in dbs:
            raise exceptions.ValidationError({"detail": "Invalid exchange market."})

        db = mongodb.get_database(db_name)

        collections = db.list_collection_names()
        if collection_name not in collections:
            raise exceptions.ValidationError({"detail": "Invalid collection."})

        collection = db.get_collection(collection_name)

        data = [item for item in collection.find(projection={"_id": False})]

        return data
