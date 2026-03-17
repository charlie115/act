import time


def terminate_process_group(owner, logger, message):
    owner.stop_restart_websocket = True
    time.sleep(0.5)
    # Support both dict (new) and list (legacy) for price_proc_event_list
    event_collection = owner.price_proc_event_list
    if isinstance(event_collection, dict):
        for event in event_collection.values():
            event.set()
    else:
        for event in event_collection:
            event.set()
    logger.info(message)

    # Give processes time to exit gracefully, then force-terminate any still alive
    time.sleep(5)
    proc_dict = getattr(owner, 'websocket_proc_dict', {})
    for proc_name, proc in list(proc_dict.items()):
        if proc.is_alive():
            logger.warning(f"Process {proc_name} still alive after event.set(), terminating...")
            proc.terminate()
            proc.join(timeout=5)

    if isinstance(owner.price_proc_event_list, dict):
        owner.price_proc_event_list = {}
    else:
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
