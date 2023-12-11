from django.conf import settings
from django_filters import FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from django_redis import get_redis_connection
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import exceptions, response, views
from pymongo import MongoClient, DESCENDING
from pytz import timezone

from infocore.models import Asset
from infocore.serializers import (
    AssetSerializer,
    AverageFundingRateDataQueryParamsSerializer,
    AverageFundingRateDataSerializer,
    FundingRateDataSerializer,
    FundingRateDataQueryParamsSerializer,
    FundingRateDiffDataQueryParamsSerializer,
    FundingRateDiffDataSerializer,
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
    appname="django-infocore-api",
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
    _prefix = "INFO_CORE|ACTIVATED|"

    def get(self, request):
        market_codes = {}
        for redis_key in REDIS_CLI.keys():
            redis_key = redis_key.decode()

            if redis_key.startswith(self._prefix):
                redis_key = redis_key.replace(self._prefix, "")

                target_market, origin_market = redis_key.split(":")
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
            past=query.get("past", ""),
            start_funding_time=query.get("start_funding_time", None),
            end_funding_time=query.get("end_funding_time", None),
            tz=query.get("tz"),
        )

        return response.Response(data)

    def get_data(
        self, market_code, base_assets, past, start_funding_time, end_funding_time, tz
    ):
        try:
            market_code, quote_asset = market_code.split("/")
        except ValueError as err:
            # TODO: Add logging
            print(err)
            raise exceptions.ValidationError()

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

        query_filter = {
            "base_asset": {"$in": base_assets},
            "quote_asset": quote_asset,
            "perpetual": True,
        }

        if start_funding_time and end_funding_time:
            query_filter["funding_time"] = {
                "$gte": start_funding_time,
                "$lte": end_funding_time,
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
        cursor_results = {base_asset: [] for base_asset in base_assets}
        for item in cursor:
            cursor_results[item["base_asset"]].append(
                FundingRateDataSerializer(item, context={"tz": tz}).data
            )

        if past:
            results = cursor_results
        else:
            results = {base_asset: [] for base_asset in base_assets}
            for key, value in cursor_results.items():
                results[key] = sorted(
                    value,
                    key=lambda v: v["datetime_now"],
                    reverse=True,
                )[:1]

        return results


@extend_schema_view(
    get=extend_schema(
        operation_id="Get average funding rate",
        description="Returns average funding rate data",
        parameters=[AverageFundingRateDataQueryParamsSerializer],
        responses={200: AverageFundingRateDataSerializer},
        tags=["FundingRate"],
    ),
)
class AverageFundingRateDataView(views.APIView):
    permission_classes = []
    page_size = 200

    def get(self, request):
        query_params = AverageFundingRateDataQueryParamsSerializer(
            data=request.query_params
        )
        query_params.is_valid(raise_exception=True)
        query = query_params.validated_data

        data = self.get_data(
            n=query.get("n", ""),
            market_code=query.get("market_code", ""),
        )

        return response.Response(data)

    def get_data(self, n, market_code):
        # Get database
        db = MONGODB_CLI.get_database("arbitrage_fundingrate")

        # Get collection
        coll = db.get_collection(f"recent_{n}_fundingrate_mean")

        # Prepare parameters
        query_filter = dict()
        if market_code:
            query_filter["market_code"] = market_code

        projection = {
            "_id": False,
        }

        # Query collection
        cursor = coll.find(
            filter=query_filter,
            projection=projection,
        )

        # Serialize
        results = [AverageFundingRateDataSerializer(item).data for item in cursor]

        return results


@extend_schema_view(
    get=extend_schema(
        operation_id="Get funding rate difference",
        description="Returns funding rate difference data",
        parameters=[FundingRateDiffDataQueryParamsSerializer],
        responses={200: FundingRateDiffDataSerializer},
        tags=["FundingRate"],
    ),
)
class FundingRateDiffDataView(views.APIView):
    permission_classes = []
    page_size = 200

    def get(self, request):
        query_params = FundingRateDiffDataQueryParamsSerializer(
            data=request.query_params
        )
        query_params.is_valid(raise_exception=True)
        query = query_params.validated_data

        data = self.get_data(
            market_code_x=query.get("market_code_x", ""),
            exchange_x=query.get("exchange_x", ""),
            market_code_y=query.get("market_code_y", ""),
            exchange_y=query.get("exchange_y", ""),
            tz=query.get("tz"),
        )

        return response.Response(data)

    def get_data(self, market_code_x, exchange_x, market_code_y, exchange_y, tz):
        # Get database
        db = MONGODB_CLI.get_database("arbitrage_fundingrate")

        # Get collection
        coll = db.get_collection("diff")

        # Prepare parameters
        query_filter = dict()
        if market_code_x:
            query_filter["market_code_x"] = market_code_x
        if exchange_x:
            query_filter["exchange_x"] = exchange_x
        if market_code_y:
            query_filter["market_code_y"] = market_code_y
        if exchange_y:
            query_filter["exchange_y"] = exchange_y

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
            FundingRateDiffDataSerializer(item, context={"tz": tz}).data
            for item in cursor
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
                asset = item["asset"]
                network = item["network_type"]

                if target_exchange not in results[asset]:
                    results[asset][target_exchange] = dict()

                if item["deposit"] is True:
                    if "deposit" not in results[asset][target_exchange]:
                        results[asset][target_exchange]["deposit"] = [network]
                    elif network not in results[asset][target_exchange]["deposit"]:
                        results[asset][target_exchange]["deposit"].append(network)

                if item["withdraw"] is True:
                    if "withdraw" not in results[asset][target_exchange]:
                        results[asset][target_exchange]["withdraw"] = [network]
                    elif network not in results[asset][target_exchange]["withdraw"]:
                        results[asset][target_exchange]["withdraw"].append(network)

        # If target and origin exchanges are the same (e.g UPBIT_SPOT/KRW, UPBIT_SPOT/BTC),
        # results won't get repeated since cursor was already exhausted in above
        # because origin cursor = target cursor
        if origin_market == "SPOT":
            # Temporary fix for huge duplicate records, source data must be fixed
            for item in origin_cursor:
                asset = item["asset"]
                network = item["network_type"]

                if origin_exchange not in results[asset]:
                    results[asset][origin_exchange] = dict()

                if item["deposit"] is True:
                    if "deposit" not in results[asset][origin_exchange]:
                        results[asset][origin_exchange]["deposit"] = [network]
                    elif network not in results[asset][origin_exchange]["deposit"]:
                        results[asset][origin_exchange]["deposit"].append(network)

                if item["withdraw"] is True:
                    if "withdraw" not in results[asset][origin_exchange]:
                        results[asset][origin_exchange]["withdraw"] = [network]
                    elif network not in results[asset][origin_exchange]["withdraw"]:
                        results[asset][origin_exchange]["withdraw"].append(network)

        return results
