from trigger.trigger import InitTrigger


class ExecutionRuntime:
    def __init__(
        self,
        admin_id,
        enabled_market_code_combinations,
        acw_api,
        redis_dict,
        postgres_db_dict,
        mongo_db_dict,
        logging_dir,
    ):
        self.trigger = InitTrigger(
            admin_id,
            enabled_market_code_combinations,
            acw_api,
            redis_dict,
            postgres_db_dict,
            mongo_db_dict,
            logging_dir,
        )

    def check_status(self, print_result=False, include_text=False):
        return self.trigger.check_status(
            print_result=print_result,
            include_text=include_text,
        )

