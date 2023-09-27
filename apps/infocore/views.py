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
    PageNumberPagination.page_size = 100

    def get(self, request):
        query_params = KlineDataQueryParamsSerializer(data=request.query_params)
        query_params.is_valid(raise_exception=True)
        query = query_params.validated_data

        data = self.get_data(
            target_market_code=query.get("target_market_code", "").replace("/", "__"),
            origin_market_code=query.get("origin_market_code", "").replace("/", "__"),
            base_asset=query.get("base_asset", ""),
            interval=query.get("interval", ""),
            start_time=query.get("start_time", None),
            end_time=query.get("end_time", None),
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
        database = f"{target_market_code}-{origin_market_code}"
        collection = f"{base_asset}_{interval}"

        # Get database
        databases = mongodb.list_database_names()
        if database not in databases:
            raise exceptions.ValidationError({"detail": "Invalid market code."})

        db = mongodb.get_database(database)

        # Get collection
        collections = db.list_collection_names()
        if collection not in collections:
            raise exceptions.ValidationError({"detail": "Invalid base asset/interval."})

        coll = db.get_collection(collection)

        # Prepare parameters
        query_filter = (
            {
                "datetime_now": {
                    "$gte": start_time,
                    "$lte": end_time,
                }
            }
            if start_time and end_time
            else {}
        )
        projection = {
            "_id": False,
        }

        # Query collection
        cursor = coll.find(
            filter=query_filter,
            projection=projection,
        )

        results = [item for item in cursor]

        return results
