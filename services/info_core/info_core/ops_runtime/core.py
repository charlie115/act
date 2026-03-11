from threading import Thread

from standalone_func.store_exchange_status import store_markets_servercheck_loop


class OpsRuntime:
    def __init__(self, acw_api, logging_dir):
        self.servercheck_thread = Thread(
            target=store_markets_servercheck_loop,
            args=(acw_api, logging_dir),
            daemon=True,
        )
        self.servercheck_thread.start()

