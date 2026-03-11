from __future__ import annotations

from dataclasses import dataclass

from execution_runtime import ExecutionRuntime
from market_runtime import MarketRuntime


@dataclass
class RuntimeComponent:
    name: str
    instance: object


class TradeCoreSupervisor:
    def __init__(
        self,
        logging_dir,
        proc_n,
        node,
        admin_id,
        acw_api,
        exchange_api_key_dict,
        postgres_db_dict,
        mongo_db_dict,
        redis_dict,
    ):
        market_runtime = MarketRuntime(
            logging_dir=logging_dir,
            proc_n=proc_n,
            node=node,
            admin_id=admin_id,
            acw_api=acw_api,
            exchange_api_key_dict=exchange_api_key_dict,
            postgres_db_dict=postgres_db_dict,
            mongo_db_dict=mongo_db_dict,
            redis_dict=redis_dict,
        )
        execution_runtime = ExecutionRuntime(
            admin_id=admin_id,
            enabled_market_code_combinations=market_runtime.enabled_market_code_combinations,
            acw_api=acw_api,
            redis_dict=market_runtime.redis_dict,
            postgres_db_dict=market_runtime.postgres_db_dict,
            mongo_db_dict=market_runtime.mogno_db_dict,
            logging_dir=market_runtime.logging_dir,
        )
        self.components = {
            "market_runtime": RuntimeComponent(
                name="market_runtime",
                instance=market_runtime,
            ),
            "execution_runtime": RuntimeComponent(
                name="execution_runtime",
                instance=execution_runtime,
            ),
        }

    def get_component(self, component_name):
        return self.components[component_name].instance

    def check_status(self, print_result=False, include_text=False):
        results = []
        for component_name in ("market_runtime", "execution_runtime"):
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
            self.get_component("market_runtime").logger.info(status_text)
        if include_text:
            return runtime_status, status_text
        return runtime_status

    def check_trade_status(self, print_result=False, include_text=False):
        return self.get_component("execution_runtime").check_status(
            print_result=print_result,
            include_text=include_text,
        )
