import time


def terminate_process_group(owner, logger, message):
    owner.stop_restart_websocket = True
    time.sleep(0.5)
    for event in owner.price_proc_event_list:
        event.set()
    logger.info(message)
    owner.price_proc_event_list = []


def restart_process_group(owner, logger, message):
    terminate_process_group(owner, logger, message)
    time.sleep(1)
    owner.stop_restart_websocket = False


def get_process_group_status(proc_dict, logger, label, *, print_result=False, include_text=False):
    if len(proc_dict) == 0:
        proc_status = False
        print_text = f"{label}websocket proc is not running."
        if print_result:
            logger.info(print_text.rstrip())
        if include_text:
            return proc_status, print_text
        return proc_status

    proc_status = all(proc.is_alive() for proc in proc_dict.values())
    print_text = ""
    for key, value in proc_dict.items():
        print_text += f"{label}{key} status: {value.is_alive()}\n"
    if print_result:
        logger.info(print_text.rstrip())
    if include_text:
        return proc_status, print_text
    return proc_status
