import logging
import hashlib
import json
import time
import pandas as pd
import pickle

from django.conf import settings
from django.core.cache import cache
from django_filters import FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import exceptions, response, views
from pymongo import DESCENDING
from pytz import timezone

from infocore.models import Asset
from infocore.models import VolatilityNotificationConfig
from platform_common.integrations.infocore import (
    get_infocore_mongo_client,
    get_infocore_redis_connection,
)
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
    KlineVolatilityQueryParamsSerializer,
    KlineVolatilitySerializer,
    WalletStatusQueryParamsSerializer,
    WalletStatusResponseSerializer,
    RankIndicatorQueryParamsSerializer,
    RankIndicatorSerializer,
    AiRankRecommendationSerializer,
    AiRankRecommendationQueryParamsSerializer,
    VolatilityNotificationConfigSerializer,
)
from lib.filters import CharArrayFilter
from lib.views import BaseViewSet

REDIS_CLI = get_infocore_redis_connection()
MONGODB_CLI = get_infocore_mongo_client(appname="django-infocore-api")
logger = logging.getLogger(__name__)


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
    http_method_names = ["get", "post"]
    permission_classes = []
    serializer_class = AssetSerializer
    filterset_class = AssetFilter
    filter_backends = [DjangoFilterBackend]


@extend_schema_view(
    get=extend_schema(
        operation_id="Get market codes",
        description="Returns list of market codes",
        tags=["MarketCodes"],
    ),
)
class MarketCodesView(views.APIView):
    http_method_names = ["get"]
    permission_classes = []
    _prefix = "INFO_CORE|ACTIVATED|"
    _index_key = "INFO_CORE|ACTIVATED_INDEX"
    _ttl_seconds = 35

    def get(self, request):
        market_codes = {}
        minimum_score = time.time() - self._ttl_seconds
        redis_keys = REDIS_CLI.zrangebyscore(self._index_key, minimum_score, "+inf")
        for redis_key in redis_keys:
            redis_key = redis_key.decode() if isinstance(redis_key, bytes) else redis_key

            target_market, origin_market = redis_key.split(":")
            if target_market in market_codes:
                market_codes[target_market].append(origin_market)
            else:
                market_codes[target_market] = [origin_market]

        data = {key: sorted(market_codes[key]) for key in sorted(market_codes.keys())}

        return response.Response(data)


@extend_schema_view(
    get=extend_schema(
        operation_id="Get current kline snapshot",
        description="Returns latest 1T now snapshot for a market combination",
        tags=["Kline"],
    ),
)
class CurrentKlineSnapshotView(views.APIView):
    http_method_names = ["get"]
    permission_classes = []

    def get(self, request):
        target_market_code = request.query_params.get("target_market_code")
        origin_market_code = request.query_params.get("origin_market_code")

        if not target_market_code or not origin_market_code:
            raise exceptions.ValidationError(
                {"detail": "target_market_code and origin_market_code are required."}
            )

        channel_name = f"INFO_CORE|{target_market_code}:{origin_market_code}_1T_now"

        try:
            latest_entries = REDIS_CLI.xrevrange(channel_name, count=1)
            if not latest_entries:
                return response.Response([])

            _, entry_data = latest_entries[0]
            kline_df = pickle.loads(entry_data[b"data"])
            concise_kline_df = kline_df.drop(
                columns=[
                    "tp_open",
                    "tp_high",
                    "tp_low",
                    "tp_close",
                    "LS_open",
                    "LS_high",
                    "LS_low",
                    "SL_open",
                    "SL_high",
                    "SL_low",
                    "datetime_now",
                ],
                errors="ignore",
            )
            return response.Response(json.loads(concise_kline_df.to_json(orient="records")))
        except Exception:
            logger.exception("Error fetching current kline snapshot")
            return response.Response([])


@extend_schema_view(
    get=extend_schema(
        operation_id="Get dollar info",
        description="Returns dollar information",
        tags=["Dollar"],
    ),
)
class DollarView(views.APIView):
    http_method_names = ["get"]
    permission_classes = []

    def get(self, request):
        redis_key = "INFO_CORE|dollar"

        try:
            data = REDIS_CLI.get(redis_key).decode()
        except AttributeError:
            raise exceptions.NotFound()

        try:
            data = json.loads(data)
        except Exception as exception:
            raise exceptions.APIException(detail=str(exception))

        return response.Response(data)
    
@extend_schema_view(
    get=extend_schema(
        operation_id="Get usdt info",
        description="Returns usdt information",
        tags=["USDT"],
    ),
)
class USDTView(views.APIView):
    http_method_names = ["get"]
    permission_classes = []

    def get(self, request):
        redis_key = "INFO_CORE|usdt"

        try:
            data = REDIS_CLI.get(redis_key).decode()
        except AttributeError:
            raise exceptions.NotFound()

        try:
            data = json.loads(data)
        except Exception as exception:
            raise exceptions.APIException(detail=str(exception))

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
    http_method_names = ["get"]
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
        operation_id="Get kline volatility",
        description="Returns kline volatility info",
        parameters=[KlineVolatilityQueryParamsSerializer],
        responses={200: KlineVolatilitySerializer},
        tags=["KlineVolatility"],
    ),
)
class KlineVolatilityView(views.APIView):
    http_method_names = ["get"]
    permission_classes = []
    page_size = 200

    def get(self, request):
        query_params = KlineVolatilityQueryParamsSerializer(data=request.query_params)
        query_params.is_valid(raise_exception=True)
        query = query_params.validated_data

        data = self.get_data(
            target_market_code=query.get("target_market_code", ""),
            origin_market_code=query.get("origin_market_code", ""),
            base_assets=query.get("base_asset", ""),
            tz=query.get("tz"),
        )

        return response.Response(data)

    def get_data(
        self,
        target_market_code,
        origin_market_code,
        base_assets,
        tz,
    ):
        try:
            database = target_market_code.replace("/", "__") + '-' + origin_market_code.replace("/", "__")
            collection = "volatility_info"

            # Get database and collection
            db = MONGODB_CLI.get_database(database)
            coll = db.get_collection(collection)

            pipeline = []
            if base_assets:
                pipeline.append({"$match": {"base_asset": {"$in": base_assets}}})

            pipeline.append({"$sort": {"datetime_now": -1}})
            pipeline.append({
                "$group": {
                    "_id": "$base_asset",
                    "data": {"$first": "$$ROOT"}
                }
            })

            cursor = coll.aggregate(pipeline)
            
            # Return a list of serialized values instead of a dictionary with base_asset keys
            results = [
                KlineVolatilitySerializer(item["data"], context={"tz": tz}).data
                for item in cursor
            ]
            return results
        except Exception:
            logger.exception("Error fetching volatility data")
            return []


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
    http_method_names = ["get"]
    permission_classes = []
    CACHE_TTL = 10  # 10 seconds - short TTL to minimize staleness

    def get(self, request):
        query_params = FundingRateDataQueryParamsSerializer(data=request.query_params)
        query_params.is_valid(raise_exception=True)
        query = query_params.validated_data

        data = self.get_data(
            market_code=query.get("market_code", ""),
            base_assets=query.get("base_asset", ""),
            last_n=query.get("last_n", None),
            start_funding_time=query.get("start_funding_time", None),
            end_funding_time=query.get("end_funding_time", None),
            tz=query.get("tz"),
        )

        return response.Response(data)

    def _get_cache_key(self, market_code, base_assets, last_n, start_funding_time, end_funding_time):
        """Generate a unique cache key based on query parameters."""
        # Sort base_assets for consistent cache key
        sorted_assets = sorted(base_assets) if base_assets else []
        key_data = f"funding_rate:{market_code}:{','.join(sorted_assets)}:{last_n}:{start_funding_time}:{end_funding_time}"
        return f"fr:{hashlib.md5(key_data.encode()).hexdigest()}"

    def get_data(
        self, market_code, base_assets, last_n, start_funding_time, end_funding_time, tz
    ):
        try:
            market_code_parsed, quote_asset = market_code.split("/")
        except ValueError as err:
            raise exceptions.ValidationError({"detail": "Invalid market code format."})

        # Check cache first (cache raw data without timezone conversion)
        cache_key = self._get_cache_key(market_code, base_assets, last_n, start_funding_time, end_funding_time)
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            # Apply timezone conversion to cached data
            return self._apply_timezone(cached_data, tz)

        database = f"{market_code_parsed.split('_')[0]}_fundingrate"
        collection = "_".join(market_code_parsed.split("_")[1:])

        # Direct database access without expensive metadata queries
        db = MONGODB_CLI.get_database(database)
        coll = db.get_collection(collection)

        # Use MongoDB aggregation pipeline for efficient server-side processing
        pipeline = [
            {
                "$match": {
                    "base_asset": {"$in": base_assets},
                    "quote_asset": quote_asset,
                    "perpetual": True,
                }
            },
        ]

        # Add time range filter if specified
        if start_funding_time and end_funding_time:
            pipeline[0]["$match"]["funding_time"] = {
                "$gte": start_funding_time,
                "$lte": end_funding_time,
            }

        # Sort and group by base_asset in MongoDB
        pipeline.extend([
            {"$sort": {"datetime_now": -1}},  # Sort descending first
            {
                "$group": {
                    "_id": "$base_asset",
                    "documents": {"$push": {
                        "symbol": "$symbol",
                        "funding_rate": "$funding_rate",
                        "funding_time": "$funding_time",
                        "funding_interval_hours": "$funding_interval_hours",
                        "datetime_now": "$datetime_now",
                    }}
                }
            },
        ])

        # Limit documents per group if last_n is specified
        if last_n != -1 and last_n is not None:
            pipeline.append({
                "$project": {
                    "_id": 1,
                    "documents": {"$slice": ["$documents", last_n]}
                }
            })

        # Execute aggregation
        cursor = coll.aggregate(pipeline)

        # Build results dict - documents are already sorted desc, reverse for asc order
        results = {}
        for item in cursor:
            base_asset = item["_id"]
            docs = item["documents"]
            docs.reverse()  # Reverse to get ascending order (oldest first)
            results[base_asset] = docs

        # Ensure all requested base_assets are in results (even if empty)
        for base_asset in base_assets:
            if base_asset not in results:
                results[base_asset] = []

        # Cache the raw results (without timezone conversion)
        cache.set(cache_key, results, self.CACHE_TTL)

        # Apply timezone conversion and serialize
        return self._apply_timezone(results, tz)

    def _apply_timezone(self, results, tz):
        """Apply timezone conversion and serialization to results."""
        serialized_results = {}
        for base_asset, docs in results.items():
            serialized_results[base_asset] = FundingRateDataSerializer(
                docs,
                many=True,
                context={"tz": tz},
            ).data
        return serialized_results


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
    http_method_names = ["get"]
    permission_classes = []
    CACHE_TTL = 10  # 10 seconds - short TTL to minimize staleness

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

    def _get_cache_key(self, n, market_code):
        """Generate a unique cache key based on query parameters."""
        return f"avg_fr:{n}:{market_code or 'all'}"

    def get_data(self, n, market_code):
        # Check cache first
        cache_key = self._get_cache_key(n, market_code)
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return cached_data

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

        # Serialize using many=True for better performance
        results = AverageFundingRateDataSerializer(list(cursor), many=True).data

        # Cache results
        cache.set(cache_key, results, self.CACHE_TTL)

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
    http_method_names = ["get"]
    permission_classes = []
    CACHE_TTL = 10  # 10 seconds - short TTL to minimize staleness

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

    def _get_cache_key(self, market_code_x, exchange_x, market_code_y, exchange_y):
        """Generate a unique cache key based on query parameters."""
        return f"fr_diff:{market_code_x or 'all'}:{exchange_x or 'all'}:{market_code_y or 'all'}:{exchange_y or 'all'}"

    def get_data(self, market_code_x, exchange_x, market_code_y, exchange_y, tz):
        # Check cache first (cache raw data without timezone conversion)
        cache_key = self._get_cache_key(market_code_x, exchange_x, market_code_y, exchange_y)
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            # Apply timezone conversion to cached data
            return FundingRateDiffDataSerializer(cached_data, many=True, context={"tz": tz}).data

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

        # Convert to list for caching (raw data without timezone conversion)
        raw_results = list(cursor)

        # Cache raw results
        cache.set(cache_key, raw_results, self.CACHE_TTL)

        # Serialize with timezone conversion using many=True
        results = FundingRateDiffDataSerializer(raw_results, many=True, context={"tz": tz}).data

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
    http_method_names = ["get"]
    permission_classes = []

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


@extend_schema_view(
    get=extend_schema(
        operation_id="Get rank indicator",
        description="Returns rank indicator using kline data, volatility data and funding rate",
        parameters=[RankIndicatorQueryParamsSerializer],
        responses={200: RankIndicatorSerializer},
        tags=["RankIndicator"],
    ),
)
class RankIndicatorView(views.APIView):
    http_method_names = ["get"]
    permission_classes = []
    
    def get(self, request):
        query_params = RankIndicatorQueryParamsSerializer(data=request.query_params)
        query_params.is_valid(raise_exception=True)
        query = query_params.validated_data
        
        target_market_code = query.get("target_market_code", "")
        origin_market_code = query.get("origin_market_code", "")
        # weights parameters
        w_ls_close = query.get("w_ls_close", -0.3)
        w_spread = query.get("w_spread", -0.35)
        w_volatility = query.get("w_volatility", 0.6)
        w_funding = query.get("w_funding", 0.1)
        w_atp = query.get("w_atp", 1.0)
                
        tz = query.get("tz")
        base_assets = query.get("base_asset")
        # convert base_assets to list
        if base_assets:
            base_assets = base_assets.split(",")
                
        # 1. Get kline data
        kline_data = self.get_kline_data(
            target_market_code=target_market_code,
            origin_market_code=origin_market_code,
        )
        
        # 2. Get volatility data
        volatility_data = self.get_volatility_data(
            target_market_code=target_market_code,
            origin_market_code=origin_market_code,
            base_assets=base_assets,
            tz=tz,
        )
        
        # 3. Get funding rate data
        funding_rate_data = self.get_funding_rate_data(
            market_code=origin_market_code,
            base_assets=base_assets,
            tz=tz,
        )
        
        # 4. Combine data and calculate indicator
        combined_data = self.rank_indicator(
            kline_data=kline_data,
            volatility_data=volatility_data,
            funding_rate_data=funding_rate_data,
            w_ls_close=w_ls_close,
            w_spread=w_spread,
            w_volatility=w_volatility,
            w_funding=w_funding,
            w_atp=w_atp,
        )
        
        return response.Response(combined_data)
    
    def get_kline_data(self, target_market_code, origin_market_code):
        # Construct Redis channel name based on websocket implementation
        channel_name = f"INFO_CORE|{target_market_code}:{origin_market_code}_1T_now"
        
        try:
            # Get latest stream entry from Redis
            stream = REDIS_CLI.xread(
                streams={channel_name: "0-0"},
                count=1,
                block=0,
            )
            
            if not stream:
                return {}

            # Unpack stream data (same as websocket consumer)
            _, entries = stream[0]
            entry_id, entry_data = entries[0]
            kline_df = pickle.loads(entry_data[b"data"])
            
            # Convert to JSON and filter by base_asset
            kline_json = json.loads(kline_df.to_json(orient="records"))            
            return kline_json
            
        except Exception:
            logger.exception("Error fetching Redis kline data")
            return {}
    
    def get_volatility_data(self, target_market_code, origin_market_code, base_assets, tz):
        try:
            database = target_market_code.replace("/", "__") + '-' + origin_market_code.replace("/", "__")
            collection = "volatility_info"

            # Get database and collection
            db = MONGODB_CLI.get_database(database)
            coll = db.get_collection(collection)

            pipeline = []
            if base_assets:
                pipeline.append({"$match": {"base_asset": {"$in": base_assets}}})

            pipeline.append({"$sort": {"datetime_now": -1}})
            pipeline.append({
                "$group": {
                    "_id": "$base_asset",
                    "data": {"$first": "$$ROOT"}
                }
            })

            cursor = coll.aggregate(pipeline)
            
            results = {
                item["_id"]: KlineVolatilitySerializer(item["data"], context={"tz": tz}).data
                for item in cursor
            }
            return results
        except Exception:
            logger.exception("Error fetching volatility data")
            return {}
    
    def get_funding_rate_data(self, market_code, base_assets, tz):
        try:
            market_code, quote_asset = market_code.split("/")
        except ValueError:
            return {}
        
        database = f"{market_code.split('_')[0]}_fundingrate"
        collection = "_".join(market_code.split("_")[1:])
        
        try:
            db = MONGODB_CLI.get_database(database)
            coll = db.get_collection(collection)
            
            # Create aggregation pipeline
            pipeline = [
                {"$match": {
                    "perpetual": True,
                    "base_asset": {"$in": base_assets} if base_assets else {"$exists": True},
                    "quote_asset": quote_asset
                }},
                {"$sort": {"funding_time": DESCENDING}},
                {"$group": {
                    "_id": "$base_asset",
                    "latest_entry": {"$first": "$$ROOT"}
                }}
            ]

            cursor = coll.aggregate(pipeline)
            
            return {
                item["_id"]: FundingRateDataSerializer(
                    item["latest_entry"], 
                    context={"tz": tz}
                ).data
                for item in cursor
            }
        except Exception:
            logger.exception("Error fetching funding rate data")
            return {}
    
    def rank_indicator(self,
                      kline_data,
                      volatility_data,
                      funding_rate_data,
                      w_ls_close,
                      w_spread,
                      w_volatility,
                      w_funding,
                      w_atp):
        """
        Combine and normalize data, then calculate indicator with weights
        """
        if not kline_data:
            return []

        # Phase 1: Collect all raw values
        features = []
        for each_kline in kline_data:
            base_asset = each_kline.get("base_asset")
            ls_close = each_kline.get("LS_close", 0)
            spread = abs(each_kline.get("LS_close", 0) - each_kline.get("SL_close", 0))
            atp24h = each_kline.get("atp24h", 0)
            volatility = volatility_data.get(base_asset, {}).get("mean_diff", 0)
            funding = funding_rate_data.get(base_asset, {}).get("funding_rate", 0)
            
            features.append({
                "base_asset": base_asset,
                "ls_close": ls_close,
                "spread": spread,
                "volatility": volatility,
                "funding": funding,
                "atp24h": atp24h
            })

        # Extract values for normalization
        ls_closes = [f["ls_close"] for f in features]
        spreads = [f["spread"] for f in features]
        volatilities = [f["volatility"] for f in features]
        fundings = [f["funding"] for f in features]
        atps = [f["atp24h"] for f in features]

        # Calculate normalization parameters
        def get_norm_params(values):
            v_min = min(values) if values else 0
            v_max = max(values) if values else 0
            return v_min, v_max, v_max - v_min

        ls_closes_min, ls_closes_max, ls_closes_range = get_norm_params(ls_closes)
        s_min, s_max, s_range = get_norm_params(spreads)
        v_min, v_max, v_range = get_norm_params(volatilities)
        f_min, f_max, f_range = get_norm_params(fundings)
        a_min, a_max, a_range = get_norm_params(atps)

        # Phase 2: Calculate normalized values
        combined_data = []
        for f in features:
            # Normalize each feature (0-1 range)
            norm_ls_close = (f["ls_close"] - ls_closes_min) / ls_closes_range if ls_closes_range != 0 else 0.5
            norm_spread = (f["spread"] - s_min) / s_range if s_range != 0 else 0.5
            norm_volatility = (f["volatility"] - v_min) / v_range if v_range != 0 else 0.5
            
            # Better funding rate normalization that preserves sign information
            if f_range != 0:
                # Center around zero and scale to [-1, 1] range
                norm_funding = f["funding"] / max(abs(f_min), abs(f_max)) if max(abs(f_min), abs(f_max)) != 0 else 0
            else:
                norm_funding = 0
                
            norm_atp = (f["atp24h"] - a_min) / a_range if a_range != 0 else 0.5
            
            # Apply weights to normalized values
            indicator_value = (
                w_ls_close * norm_ls_close +
                w_spread * norm_spread +
                w_volatility * norm_volatility +
                w_funding * norm_funding +
                w_atp * norm_atp
            )

            combined_data.append({
                "base_asset": f["base_asset"],
                "indicator_value": indicator_value,
                # Include normalized values for debugging:
                "_normalized": {
                    "ls_close": norm_ls_close,
                    "spread": norm_spread,
                    "volatility": norm_volatility,
                    "funding": norm_funding,
                    "atp24h": norm_atp
                }
            })

        # Sort and rank
        combined_data.sort(key=lambda x: x["indicator_value"], reverse=True)
        for rank, item in enumerate(combined_data, 1):
            item["rank"] = rank
            # Remove debug info in production
            # del item["_normalized"]

        return combined_data


@extend_schema_view(
    get=extend_schema(
        operation_id="Get AI rank recommendations",
        description="Returns AI-generated recommendations with rank information",
        parameters=[AiRankRecommendationQueryParamsSerializer],
        responses={200: AiRankRecommendationSerializer(many=True)},
        tags=["AI Recommendations"],
    ),
)
class AiRankRecommendationView(views.APIView):
    http_method_names = ["get"]
    permission_classes = []
    
    def get(self, request):
        try:
            query_params = AiRankRecommendationQueryParamsSerializer(data=request.query_params)
            query_params.is_valid(raise_exception=True)
            query = query_params.validated_data
            
            target_market_code = query.get("target_market_code", "").replace("/", "__")
            origin_market_code = query.get("origin_market_code", "").replace("/", "__")
            
            # Construct database name following the pattern in KlineDataView
            database = f"{target_market_code}-{origin_market_code}"
            collection_name = 'ai_recommendation_info'
            
            # Check if database exists
            databases = MONGODB_CLI.list_database_names()
            if database not in databases:
                return response.Response(
                    {"detail": f"Invalid market code combination: {target_market_code}-{origin_market_code}"},
                    status=404
                )
            
            db = MONGODB_CLI.get_database(database)
            
            # Check if collection exists
            collections = db.list_collection_names()
            if collection_name not in collections:
                return response.Response(
                    {"detail": f"Collection '{collection_name}' not found in database '{database}'."},
                    status=404
                )
            
            # Get collection
            coll = db.get_collection(collection_name)
            
            # Fetch all documents from the collection
            cursor = coll.find(
                filter={},
                projection={"_id": False}
            ).sort("rank", 1)  # Sort by rank in ascending order
            
            # Serialize the data
            results = [AiRankRecommendationSerializer(item).data for item in cursor]
            
            return response.Response(results)
            
        except Exception as e:
            return response.Response(
                {"detail": f"Error fetching AI recommendation data: {str(e)}"},
                status=500
            )


@extend_schema(tags=["Volatility Notification"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List volatility notification configs",
        description="Returns a list of the user's volatility notification configurations.",
    ),
    create=extend_schema(
        operation_id="Create volatility notification config",
        description="Creates a new volatility notification configuration for the current user.",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve volatility notification config",
        description="Retrieves details of an existing volatility notification configuration.",
    ),
    update=extend_schema(
        operation_id="Update volatility notification config",
        description="Fully updates an existing volatility notification configuration.",
    ),
    partial_update=extend_schema(
        operation_id="Partial update volatility notification config",
        description="Partially updates an existing volatility notification configuration.",
    ),
    destroy=extend_schema(
        operation_id="Delete volatility notification config",
        description="Deletes an existing volatility notification configuration.",
    ),
)
class VolatilityNotificationConfigViewSet(BaseViewSet):
    """
    ViewSet for managing user's volatility notification configurations.

    Users can create, view, update, and delete their own notification configs.
    When volatility exceeds the configured threshold, a notification message
    will be created and sent via Telegram.
    """

    queryset = VolatilityNotificationConfig.objects.all()
    serializer_class = VolatilityNotificationConfigSerializer
    http_method_names = ["get", "post", "put", "patch", "delete"]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["target_market_code", "origin_market_code", "enabled"]

    def get_queryset(self):
        """Filter to only show the current user's configs."""
        queryset = super().get_queryset()
        if self.request.user and self.request.user.is_authenticated:
            return queryset.filter(user=self.request.user)
        return queryset.none()
