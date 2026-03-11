from analytics_runtime import AnalyticsRuntime
from kline_runtime import KlineRuntime
from market_ingest import MarketIngestRuntime
from ops_runtime import OpsRuntime


class InitCore:
    def __init__(
        self,
        logging_dir,
        master_flag,
        proc_n,
        node,
        admin_id,
        acw_api,
        ai_api_key,
        exchange_api_key_dict,
        enabled_market_klines,
        enabled_arbitrage_markets,
        mongodb_dict,
        redis_dict,
    ):
        self.ops_runtime = OpsRuntime(acw_api=acw_api, logging_dir=logging_dir)
        self.market_ingest = MarketIngestRuntime(
            logging_dir=logging_dir,
            proc_n=proc_n,
            node=node,
            admin_id=admin_id,
            acw_api=acw_api,
            exchange_api_key_dict=exchange_api_key_dict,
            enabled_market_klines=enabled_market_klines,
            mongodb_dict=mongodb_dict,
            redis_dict=redis_dict,
        )
        self.analytics_runtime = AnalyticsRuntime(
            master_flag=master_flag,
            admin_id=admin_id,
            node=node,
            acw_api=acw_api,
            logging_dir=logging_dir,
            mongodb_dict=mongodb_dict,
            redis_dict=redis_dict,
            ai_api_key=ai_api_key,
            exchange_api_key_dict=exchange_api_key_dict,
            enabled_arbitrage_markets=enabled_arbitrage_markets,
        )
        self.kline_runtime = KlineRuntime(
            admin_id=admin_id,
            node=node,
            enabled_market_klines=enabled_market_klines,
            acw_api=acw_api,
            redis_dict=redis_dict,
            mongodb_dict=mongodb_dict,
            logging_dir=logging_dir,
        )

    def __getattr__(self, name):
        for component_name in (
            "market_ingest",
            "analytics_runtime",
            "kline_runtime",
            "ops_runtime",
        ):
            component = object.__getattribute__(self, component_name)
            if hasattr(component, name):
                return getattr(component, name)
        raise AttributeError(f"{self.__class__.__name__!s} has no attribute {name!r}")

    def check_status(self, print_result=False, include_text=False):
        return self.market_ingest.check_status(
            print_result=print_result,
            include_text=include_text,
        )

    def check_kline_status(self, print_result=False, include_text=False):
        return self.kline_runtime.check_status(
            print_result=print_result,
            include_text=include_text,
        )
