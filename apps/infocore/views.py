from django.conf import settings
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import exceptions, response, views
from pymongo import MongoClient, DESCENDING
from pytz import timezone

from infocore.serializers import KlineDataDataSerializer, KlineDataQueryParamsSerializer


MONGODB_CLI = MongoClient(
    host=settings.MONGODB["HOST"],
    port=settings.MONGODB["PORT"],
    username=settings.MONGODB["USERNAME"],
    password=settings.MONGODB["PASSWORD"],
)


@extend_schema_view(
    get=extend_schema(
        operation_id="Get kline data",
        description="Returns kline data",
        parameters=[KlineDataQueryParamsSerializer],
        responses={200: KlineDataDataSerializer},
        tags=["Kline"],
    ),
)
class KlineDataView(views.APIView):
    permission_classes = []
    page_size = 200

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
            tz=query.get("tz"),
        )

        return response.Response(data)

    def get_data(
        self,
        target_market_code,
        origin_market_code,
        base_asset,
        interval,
        start_time,
        end_time,
        tz,
    ):
        if start_time and end_time:
            start_time = timezone(tz).localize(start_time.replace(tzinfo=None))
            end_time = timezone(tz).localize(end_time.replace(tzinfo=None))

        database = f"{target_market_code}-{origin_market_code}"
        collection = f"{base_asset}_{interval}"

        # Get database
        databases = MONGODB_CLI.list_database_names()
        if database not in databases:
            raise exceptions.ValidationError({"detail": "Invalid market code."})

        db = MONGODB_CLI.get_database(database)

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

        # If no start_time and end_time, get latest n data
        if not (start_time and end_time):
            cursor = cursor.sort("datetime_now", DESCENDING).limit(self.page_size)

        # Sort back for display
        results = [
            {
                key: value for key, value in item.items() if key != "record_count"
            }  # FIXME: Debugging
            for item in cursor
        ]
        results = sorted(results, key=lambda item: item["datetime_now"])

        return results
