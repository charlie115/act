from supervisor import TradeCoreSupervisor


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
        self.supervisor = TradeCoreSupervisor(
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
        self.market_runtime = self.supervisor.get_component("market_runtime")
        self.execution_runtime = self.supervisor.get_component("execution_runtime")

    def __getattr__(self, name):
        market_runtime = object.__getattribute__(self, "market_runtime")
        if hasattr(market_runtime, name):
            return getattr(market_runtime, name)

        execution_runtime = object.__getattribute__(self, "execution_runtime")
        if hasattr(execution_runtime, name):
            return getattr(execution_runtime, name)

        raise AttributeError(f"{self.__class__.__name__!s} has no attribute {name!r}")

    def check_status(self, print_result=False, include_text=False):
        return self.supervisor.check_status(
            print_result=print_result,
            include_text=include_text,
        )

    def check_trade_status(self, print_result=False, include_text=False):
        return self.supervisor.check_trade_status(
            print_result=print_result,
            include_text=include_text,
        )

    def stop(self):
        return self.supervisor.stop()

    def restart(self):
        return self.supervisor.restart()
