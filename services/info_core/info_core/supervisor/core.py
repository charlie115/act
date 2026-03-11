from __future__ import annotations

from dataclasses import dataclass
import os
import sys

from analytics_runtime import AnalyticsRuntime
from kline_runtime import KlineRuntime
from market_ingest import MarketIngestRuntime
from ops_runtime import OpsRuntime


@dataclass
class RuntimeComponent:
    name: str
    instance: object


class InfoCoreSupervisor:
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
        self.components = {
            "ops_runtime": RuntimeComponent(
                name="ops_runtime",
                instance=OpsRuntime(acw_api=acw_api, logging_dir=logging_dir),
            ),
            "market_ingest": RuntimeComponent(
                name="market_ingest",
                instance=MarketIngestRuntime(
                    logging_dir=logging_dir,
                    authoritative_reference_publisher=master_flag,
                    proc_n=proc_n,
                    node=node,
                    admin_id=admin_id,
                    acw_api=acw_api,
                    exchange_api_key_dict=exchange_api_key_dict,
                    enabled_market_klines=enabled_market_klines,
                    mongodb_dict=mongodb_dict,
                    redis_dict=redis_dict,
                ),
            ),
            "analytics_runtime": RuntimeComponent(
                name="analytics_runtime",
                instance=AnalyticsRuntime(
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
                ),
            ),
            "kline_runtime": RuntimeComponent(
                name="kline_runtime",
                instance=KlineRuntime(
                    admin_id=admin_id,
                    node=node,
                    enabled_market_klines=enabled_market_klines,
                    acw_api=acw_api,
                    redis_dict=redis_dict,
                    mongodb_dict=mongodb_dict,
                    logging_dir=logging_dir,
                ),
            ),
        }
        self.module_name = "info_core_main"

    def get_component(self, component_name):
        return self.components[component_name].instance

    def iter_components(self):
        for component_name in (
            "market_ingest",
            "analytics_runtime",
            "kline_runtime",
            "ops_runtime",
        ):
            yield component_name, self.get_component(component_name)

    def check_status(self, print_result=False, include_text=False):
        results = []
        for component_name in ("market_ingest", "analytics_runtime", "ops_runtime"):
            component = self.get_component(component_name)
            if hasattr(component, "check_status"):
                component_status, component_text = component.check_status(include_text=True)
                results.append((component_name, component_status, component_text))

        runtime_status = all(result[1] for result in results) if results else True
        status_text = "\n".join(
            f"[{component_name}] {component_text}"
            for component_name, _, component_text in results
        )
        if print_result and status_text:
            self.get_component("market_ingest").logger.info(status_text)
        if include_text:
            return runtime_status, status_text
        return runtime_status

    def check_kline_status(self, print_result=False, include_text=False):
        return self.get_component("kline_runtime").check_status(
            print_result=print_result,
            include_text=include_text,
        )

    def shutdown(self):
        for component_name in ("ops_runtime", "kline_runtime", "analytics_runtime", "market_ingest"):
            component = self.get_component(component_name)
            if hasattr(component, "shutdown"):
                component.shutdown()

    def stop(self):
        self.shutdown()
        raise SystemExit(0)

    def restart(self):
        self.shutdown()
        os.execv(sys.executable, [sys.executable, "-m", self.module_name, *sys.argv[1:]])
