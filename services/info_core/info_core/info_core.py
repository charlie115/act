from supervisor import InfoCoreSupervisor


class InitCore:
    def __init__(
        self,
        logging_dir,
        master_flag,
        run_funding_updater,
        run_wallet_status_updater,
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
        self.supervisor = InfoCoreSupervisor(
            logging_dir=logging_dir,
            master_flag=master_flag,
            run_funding_updater=run_funding_updater,
            run_wallet_status_updater=run_wallet_status_updater,
            proc_n=proc_n,
            node=node,
            admin_id=admin_id,
            acw_api=acw_api,
            ai_api_key=ai_api_key,
            exchange_api_key_dict=exchange_api_key_dict,
            enabled_market_klines=enabled_market_klines,
            enabled_arbitrage_markets=enabled_arbitrage_markets,
            mongodb_dict=mongodb_dict,
            redis_dict=redis_dict,
        )
        self.market_ingest = self.supervisor.get_component("market_ingest")
        self.analytics_runtime = self.supervisor.get_component("analytics_runtime")
        self.kline_runtime = self.supervisor.get_component("kline_runtime")
        self.ops_runtime = self.supervisor.get_component("ops_runtime")

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
        return self.supervisor.check_status(
            print_result=print_result,
            include_text=include_text,
        )

    def check_kline_status(self, print_result=False, include_text=False):
        return self.supervisor.check_kline_status(
            print_result=print_result,
            include_text=include_text,
        )

    def stop(self):
        return self.supervisor.stop()

    def restart(self):
        return self.supervisor.restart()
