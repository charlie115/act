import pymongo
from django.conf import settings
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import exceptions, views
from rest_framework.pagination import PageNumberPagination


from infocore.serializers import KlineDataDataSerializer, KlineDataQueryParamsSerializer


mongodb = pymongo.MongoClient(settings.MONGODB["HOST"], settings.MONGODB["PORT"])


@extend_schema_view(
    get=extend_schema(
        operation_id="Get kline data",
        description="Returns kline data",
        parameters=[KlineDataQueryParamsSerializer],
        responses={200: KlineDataDataSerializer},
        tags=["Kline"],
    ),
)
class KlineDataView(views.APIView, PageNumberPagination):
    permission_classes = []
    PageNumberPagination.page_size = 200

    def get(self, request):
        query_params = KlineDataQueryParamsSerializer(data=request.query_params)
        query_params.is_valid(raise_exception=True)
        query = query_params.validated_data

        data = self.get_data(
            target_market_code=query["target_market_code"].replace("/", "__"),
            origin_market_code=query["origin_market_code"].replace("/", "__"),
            base_asset=query["base_asset"],
            interval=query["interval"],
            start_time=query["start_time"],
            end_time=query["end_time"],
        )

        return self.get_paginated_response(self.paginate_queryset(data, request))

    def get_data(
        self,
        target_market_code,
        origin_market_code,
        base_asset,
        interval,
        start_time,
        end_time,
    ):
        db_name = f"{target_market_code}-{origin_market_code}"
        collection_name = f"{base_asset}_{interval}"

        dbs = mongodb.list_database_names()
        if db_name not in dbs:
            raise exceptions.ValidationError({"detail": "Invalid market code."})

        db = mongodb.get_database(db_name)

        collections = db.list_collection_names()
        if collection_name not in collections:
            raise exceptions.ValidationError({"detail": "Invalid base asset/interval."})

        collection = db.get_collection(collection_name)

        data = [item for item in collection.find(projection={"_id": False})]

        return data
