from execution_runtime import ExecutionRuntime
from market_runtime import MarketRuntime


class InitCore:
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
        self.market_runtime = MarketRuntime(
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
        self.execution_runtime = ExecutionRuntime(
            admin_id=admin_id,
            enabled_market_code_combinations=self.market_runtime.enabled_market_code_combinations,
            acw_api=acw_api,
            redis_dict=self.market_runtime.redis_dict,
            postgres_db_dict=self.market_runtime.postgres_db_dict,
            mongo_db_dict=self.market_runtime.mogno_db_dict,
            logging_dir=self.market_runtime.logging_dir,
        )

    def __getattr__(self, name):
        market_runtime = object.__getattribute__(self, "market_runtime")
        if hasattr(market_runtime, name):
            return getattr(market_runtime, name)

        execution_runtime = object.__getattribute__(self, "execution_runtime")
        if hasattr(execution_runtime, name):
            return getattr(execution_runtime, name)

        raise AttributeError(f"{self.__class__.__name__!s} has no attribute {name!r}")

    def check_status(self, print_result=False, include_text=False):
        return self.market_runtime.check_status(
            print_result=print_result,
            include_text=include_text,
        )

    def check_trade_status(self, print_result=False, include_text=False):
        return self.execution_runtime.check_status(
            print_result=print_result,
            include_text=include_text,
        )
