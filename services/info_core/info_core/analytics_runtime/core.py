from multiprocessing import Process

from aidata_generator.aidata_core import InitAiDataCore
from arbitrage_generator.arbitrage_core import InitAbitrageCore
from standalone_func.wallet_funding_updater import start_wallet_funding_update


class AnalyticsRuntime:
    def __init__(
        self,
        master_flag,
        admin_id,
        node,
        acw_api,
        logging_dir,
        mongodb_dict,
        redis_dict,
        ai_api_key,
        exchange_api_key_dict,
        enabled_arbitrage_markets,
    ):
        self.master_flag = master_flag
        self.wallet_funding_update_proc = None
        self.arbitrage_generator = None
        self.ai_data_generator = None

        if not master_flag:
            return

        self.wallet_funding_update_proc = Process(
            target=start_wallet_funding_update,
            args=(admin_id, node, acw_api, logging_dir, mongodb_dict, exchange_api_key_dict),
            daemon=True,
        )
        self.wallet_funding_update_proc.start()

        self.arbitrage_generator = InitAbitrageCore(
            admin_id,
            node,
            acw_api,
            enabled_arbitrage_markets,
            mongodb_dict,
            logging_dir,
        )

        self.ai_data_generator = InitAiDataCore(
            admin_id,
            node,
            acw_api,
            ai_api_key,
            redis_dict,
            mongodb_dict,
            logging_dir,
        )
        self.ai_data_generator.start_aidata_generator()

    def check_status(self, print_result=False, include_text=False):
        if not self.master_flag:
            status_text = "analytics_runtime disabled on non-master node"
            if include_text:
                return True, status_text
            return True

        results = []

        wallet_status = self.wallet_funding_update_proc is not None and self.wallet_funding_update_proc.is_alive()
        results.append(("wallet_funding_update_proc", wallet_status))

        if self.arbitrage_generator is not None:
            arbitrage_status, arbitrage_text = self.arbitrage_generator.check_status(include_text=True)
            results.append(("arbitrage_generator", arbitrage_status, arbitrage_text))
        else:
            results.append(("arbitrage_generator", False, "arbitrage_generator not initialized"))

        if self.ai_data_generator is not None:
            ai_status, ai_text = self.ai_data_generator.check_status(include_text=True)
            results.append(("ai_data_generator", ai_status, ai_text))
        else:
            results.append(("ai_data_generator", False, "ai_data_generator not initialized"))

        runtime_status = all(item[1] for item in results)
        status_lines = []
        for item in results:
            component_name = item[0]
            component_status = item[1]
            component_text = item[2] if len(item) > 2 else f"{component_name} is {'alive' if component_status else 'dead'}"
            status_lines.append(component_text)

        status_text = "\n".join(status_lines)
        if print_result and status_text:
            if self.ai_data_generator is not None:
                self.ai_data_generator.logger.info(status_text)
        if include_text:
            return runtime_status, status_text
        return runtime_status
