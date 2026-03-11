from kline_generator.kline_core import InitKlineCore


class KlineRuntime:
    def __init__(
        self,
        admin_id,
        node,
        enabled_market_klines,
        acw_api,
        redis_dict,
        mongodb_dict,
        logging_dir,
    ):
        self.kline_generator = InitKlineCore(
            admin_id,
            node,
            enabled_market_klines,
            acw_api,
            redis_dict,
            mongodb_dict,
            logging_dir,
        )

    def check_status(self, print_result=False, include_text=False):
        kline_generator_proc_dict = self.kline_generator.kline_proc_dict
        print_text = ""
        for key, value in kline_generator_proc_dict.items():
            if not value.is_alive():
                print_text += f"{key} is dead\n"
            else:
                print_text += f"{key} is alive\n"
        if print_result:
            self.kline_generator.kline_logger.info(print_text.rstrip())
        if include_text:
            return all([x.is_alive() for x in kline_generator_proc_dict.values()]), print_text
        return all([x.is_alive() for x in kline_generator_proc_dict.values()])
