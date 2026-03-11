from threading import Thread

from loggers.logger import InfoCoreLogger
from standalone_func.store_exchange_status import store_markets_servercheck_loop


class OpsRuntime:
    def __init__(self, acw_api, logging_dir):
        self.logger = InfoCoreLogger("ops_runtime", logging_dir).logger
        self.servercheck_thread = Thread(
            target=store_markets_servercheck_loop,
            args=(acw_api, logging_dir),
            daemon=True,
        )
        self.servercheck_thread.start()

    def check_status(self, print_result=False, include_text=False):
        runtime_status = self.servercheck_thread.is_alive()
        status_text = (
            "servercheck_thread is alive"
            if runtime_status
            else "servercheck_thread is dead"
        )
        if print_result:
            self.logger.info(status_text)
        if include_text:
            return runtime_status, status_text
        return runtime_status

    def shutdown(self):
        return
