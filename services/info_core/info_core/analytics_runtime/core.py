from multiprocessing import Process

from aidata_generator.aidata_core import InitAiDataCore
from arbitrage_generator.arbitrage_core import InitAbitrageCore
from standalone_func.funding_updater import start_funding_update
from standalone_func.wallet_status_updater import start_wallet_status_update


class AnalyticsRuntime:
    def __init__(
        self,
        master_flag,
        run_funding_updater,
        run_wallet_status_updater,
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
        self.run_funding_updater = run_funding_updater
        self.run_wallet_status_updater = run_wallet_status_updater
        self.funding_update_proc = None
        self.wallet_status_update_proc = None
        self.arbitrage_generator = None
        self.ai_data_generator = None

        if self.run_funding_updater:
            self.funding_update_proc = Process(
                target=start_funding_update,
                args=(admin_id, node, acw_api, logging_dir, mongodb_dict, exchange_api_key_dict),
                daemon=True,
            )
            self.funding_update_proc.start()

        if self.run_wallet_status_updater:
            self.wallet_status_update_proc = Process(
                target=start_wallet_status_update,
                args=(admin_id, node, acw_api, logging_dir, mongodb_dict, exchange_api_key_dict),
                daemon=True,
            )
            self.wallet_status_update_proc.start()

        if master_flag:
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
        results = []

        if self.run_funding_updater:
            funding_status = self.funding_update_proc is not None and self.funding_update_proc.is_alive()
            results.append(("funding_update_proc", funding_status))
        else:
            results.append(("funding_update_proc", True, "funding_update_proc disabled"))

        if self.run_wallet_status_updater:
            wallet_status = (
                self.wallet_status_update_proc is not None
                and self.wallet_status_update_proc.is_alive()
            )
            results.append(("wallet_status_update_proc", wallet_status))
        else:
            results.append(("wallet_status_update_proc", True, "wallet_status_update_proc disabled"))

        if self.master_flag and self.arbitrage_generator is not None:
            arbitrage_status, arbitrage_text = self.arbitrage_generator.check_status(include_text=True)
            results.append(("arbitrage_generator", arbitrage_status, arbitrage_text))
        elif self.master_flag:
            results.append(("arbitrage_generator", False, "arbitrage_generator not initialized"))
        else:
            results.append(("arbitrage_generator", True, "arbitrage_generator disabled on non-master node"))

        if self.master_flag and self.ai_data_generator is not None:
            ai_status, ai_text = self.ai_data_generator.check_status(include_text=True)
            results.append(("ai_data_generator", ai_status, ai_text))
        elif self.master_flag:
            results.append(("ai_data_generator", False, "ai_data_generator not initialized"))
        else:
            results.append(("ai_data_generator", True, "ai_data_generator disabled on non-master node"))

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

    def shutdown(self):
        if self.funding_update_proc is not None and self.funding_update_proc.is_alive():
            self.funding_update_proc.terminate()
            self.funding_update_proc.join(timeout=5)
        if self.wallet_status_update_proc is not None and self.wallet_status_update_proc.is_alive():
            self.wallet_status_update_proc.terminate()
            self.wallet_status_update_proc.join(timeout=5)
        if self.arbitrage_generator is not None and hasattr(self.arbitrage_generator, "shutdown"):
            self.arbitrage_generator.shutdown()
        if self.ai_data_generator is not None and hasattr(self.ai_data_generator, "shutdown"):
            self.ai_data_generator.shutdown()
