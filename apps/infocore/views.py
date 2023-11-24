from django.conf import settings
from django_filters import FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from django_redis import get_redis_connection
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import exceptions, response, views
from pymongo import MongoClient, ASCENDING, DESCENDING
from pytz import timezone

from infocore.models import Asset
from infocore.serializers import (
    AssetSerializer,
    FundingRateDataSerializer,
    FundingRateDataQueryParamsSerializer,
    KlineDataSerializer,
    KlineDataQueryParamsSerializer,
    WalletStatusQueryParamsSerializer,
    WalletStatusResponseSerializer,
)
from lib.filters import CharArrayFilter
from lib.views import BaseViewSet


REDIS_CLI = get_redis_connection("default")

MONGODB_CLI = MongoClient(
    host=settings.MONGODB["HOST"],
    port=settings.MONGODB["PORT"],
    username=settings.MONGODB["USERNAME"],
    password=settings.MONGODB["PASSWORD"],
)


class AssetFilter(FilterSet):
    symbol = CharArrayFilter(field_name="symbol", lookup_expr="in")

    class Meta:
        model = Asset
        fields = ("symbol",)


@extend_schema(tags=["Asset"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List assets",
        description="Returns a list of assets",
    ),
    create=extend_schema(
        operation_id="Add a new asset",
        description="Adds a new asset.",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve an asset",
        description="Retrieve details of an existing asset.",
    ),
)
class AssetViewSet(BaseViewSet):
    queryset = Asset.objects.all().order_by("symbol")
    serializer_class = AssetSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = AssetFilter
    http_method_names = ["get", "post"]
    permission_classes = []


@extend_schema_view(
    get=extend_schema(
        operation_id="Get market codes",
        description="Returns list of market codes",
        tags=["MarketCodes"],
    ),
)
class MarketCodesView(views.APIView):
    permission_classes = []
    page_size = 200

    def get(self, request):
        channels = REDIS_CLI.pubsub_channels()

        market_codes = {}
        for channel in channels:
            channel = channel.decode()

            if channel.startswith("INFO_CORE|") and channel.endswith("_1T_kline"):
                channel = channel.replace("INFO_CORE|", "").replace("_1T_kline", "")

                target_market, origin_market = channel.split(":")
                if target_market in market_codes:
                    market_codes[target_market].append(origin_market)
                else:
                    market_codes[target_market] = [origin_market]

        data = {key: sorted(market_codes[key]) for key in sorted(market_codes.keys())}

        return response.Response(data)


@extend_schema_view(
    get=extend_schema(
        operation_id="Get kline data",
        description="Returns kline data",
        parameters=[KlineDataQueryParamsSerializer],
        responses={200: KlineDataSerializer},
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

        # Serialize and sort back for display
        results = sorted(
            [KlineDataSerializer(item, context={"tz": tz}).data for item in cursor],
            key=lambda item: item["datetime_now"],
        )

        return results


@extend_schema_view(
    get=extend_schema(
        operation_id="Get funding rate",
        description="Returns funding rate data",
        parameters=[FundingRateDataQueryParamsSerializer],
        responses={200: FundingRateDataSerializer},
        tags=["FundingRate"],
    ),
)
class FundingRateDataView(views.APIView):
    permission_classes = []
    page_size = 200

    def get(self, request):
        query_params = FundingRateDataQueryParamsSerializer(data=request.query_params)
        query_params.is_valid(raise_exception=True)
        query = query_params.validated_data

        data = self.get_data(
            market_code=query.get("market_code", ""),
            base_assets=query.get("base_asset", ""),
            tz=query.get("tz"),
        )

        return response.Response(data)

    def get_data(self, market_code, base_assets, tz):
        market_code, quote_asset = market_code.split("/")

        database = f"{market_code.split('_')[0]}_fundingrate"
        collection = "_".join(market_code.split("_")[1:])

        # Get database
        databases = MONGODB_CLI.list_database_names()
        if database not in databases:
            raise exceptions.ValidationError({"detail": "Invalid market code."})

        db = MONGODB_CLI.get_database(database)

        # Get collection
        collections = db.list_collection_names()
        if collection not in collections:
            raise exceptions.ValidationError({"detail": "Invalid market code."})

        coll = db.get_collection(collection)

        latest_dates = coll.aggregate(
            [
                {
                    "$match": {
                        "base_asset": {"$in": base_assets} if base_assets else {},
                        "quote_asset": quote_asset,
                    }
                },
                {"$sort": {"datetime_now": ASCENDING}},
                {
                    "$group": {
                        "_id": "$base_asset",
                        "datetime_now": {"$last": "$datetime_now"},
                    }
                },
            ]
        )
        latest_dates = {item["_id"]: item["datetime_now"] for item in latest_dates}

        # Prepare parameters
        and_cond = list()
        for base_asset, datetime_now in latest_dates.items():
            query = {
                "$and": [
                    {
                        "base_asset": base_asset,
                        "quote_asset": quote_asset,
                        "perpetual": True,
                        "datetime_now": {"$eq": datetime_now},
                    }
                ]
            }
            and_cond.append(query)

        if not and_cond:
            raise exceptions.ValidationError()

        query_filter = {
            "$or": and_cond,
        }
        projection = {
            "_id": False,
        }

        # Query collection
        cursor = coll.find(
            filter=query_filter,
            projection=projection,
        )

        # Serialize
        results = [
            FundingRateDataSerializer(item, context={"tz": tz}).data for item in cursor
        ]

        return results


@extend_schema_view(
    get=extend_schema(
        operation_id="Get wallet status",
        description="Returns wallet status of assets whether transfer is possible "
        "between 2 exchanges.<br><br>"
        "Transfer is possible if: <br>"
        "`target exchange`'s ***withdraw*** network is also available in <br>"
        "`origin exchange`'s ***deposit*** network.",
        parameters=[WalletStatusQueryParamsSerializer],
        responses={200: WalletStatusResponseSerializer},
        tags=["WalletStatus"],
    ),
)
class WalletStatusView(views.APIView):
    permission_classes = []
    page_size = 200

    def get(self, request):
        query_params = WalletStatusQueryParamsSerializer(data=request.query_params)
        query_params.is_valid(raise_exception=True)
        query = query_params.validated_data

        data = self.get_data(
            target_market_code=query.get("target_market_code", ""),
            origin_market_code=query.get("origin_market_code", ""),
            base_assets=query.get("base_asset", ""),
        )

        return response.Response(data)

    def get_data(self, target_market_code, origin_market_code, base_assets):
        target_market_code = target_market_code.split("/")[0]
        origin_market_code = origin_market_code.split("/")[0]

        target_exchange = target_market_code.split("_")[0]
        origin_exchange = origin_market_code.split("_")[0]

        target_market = target_market_code.replace(f"{target_exchange}_", "")
        origin_market = origin_market_code.replace(f"{origin_exchange}_", "")

        db = MONGODB_CLI.get_database("wallet_status")

        # Get collection
        collections = db.list_collection_names()
        if not (target_exchange in collections and origin_exchange in collections):
            raise exceptions.ValidationError({"detail": "Invalid exchange."})

        # Prepare parameters
        query_filter = dict()
        if base_assets:
            query_filter["asset"] = {"$in": base_assets}
        projection = {
            "_id": False,
        }

        # Query collection
        target_coll = db.get_collection(target_exchange)
        target_cursor = target_coll.find(
            filter=query_filter,
            projection=projection,
        )

        if target_exchange == origin_exchange:
            origin_coll = target_coll
            origin_cursor = target_cursor

        else:
            origin_coll = db.get_collection(origin_exchange)
            origin_cursor = origin_coll.find(
                filter=query_filter,
                projection=projection,
            )

        # Serialize
        results = {asset: dict() for asset in base_assets}
        if target_market == "SPOT":
            for item in target_cursor:
                asset = item.pop("asset")
                network = item.pop("network_type")

                if target_exchange not in results[asset]:
                    results[asset][target_exchange] = dict()

                if item["deposit"] is True:
                    if "deposit" in results[asset][target_exchange]:
                        results[asset][target_exchange]["deposit"].append(network)
                    else:
                        results[asset][target_exchange]["deposit"] = [network]

                if item["withdraw"] is True:
                    if "withdraw" in results[asset][target_exchange]:
                        results[asset][target_exchange]["withdraw"].append(network)
                    else:
                        results[asset][target_exchange]["withdraw"] = [network]

        # If target and origin exchanges are the same (e.g UPBIT_SPOT/KRW, UPBIT_SPOT/BTC),
        # results won't get repeated since cursor was already exhausted in above
        # because origin cursor = target cursor
        if origin_market == "SPOT":
            for item in origin_cursor:
                asset = item.pop("asset")
                network = item.pop("network_type")

                if origin_exchange not in results[asset]:
                    results[asset][origin_exchange] = dict()

                if item["deposit"] is True:
                    if "deposit" in results[asset][origin_exchange]:
                        results[asset][origin_exchange]["deposit"].append(network)
                    else:
                        results[asset][origin_exchange]["deposit"] = [network]

                if item["withdraw"] is True:
                    if "withdraw" in results[asset][origin_exchange]:
                        results[asset][origin_exchange]["withdraw"].append(network)
                    else:
                        results[asset][origin_exchange]["withdraw"] = [network]

        return results
