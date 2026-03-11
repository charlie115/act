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

