import os
import sys
import argparse
import time
import traceback

from runtime_config import ConfigValidationError, load_runtime_config

def get_arguments():
    """
    Parsing arguments
    """
    current_file_dir = os.path.realpath(__file__)
    current_folder_dir = os.path.abspath(os.path.join(current_file_dir, os.pardir))
    logging_dir = f"{current_folder_dir}/loggers/logs/"

    parser = argparse.ArgumentParser()
    # parser.add_argument('--node', '-n', required=True, nargs=1, help='Specify a node name. Configuration will be done based on the node name.', dest='node')
    parser.add_argument('--proc_n', '-p', nargs=1, help='Specify a number of processes to handle websockets.', default=[None], dest='proc_n')
    parser.add_argument('--log', '-l', nargs=1, help='Specify a directory to save log files.', default=[logging_dir], dest='logging_dir')
    parser.add_argument('--config', '-c', nargs=1, help='Specify a directory of a config json file.', default=[current_folder_dir+"/.env"], dest='config_dir')

    proc_n = int(parser.parse_args().proc_n[0]) if parser.parse_args().proc_n[0] is not None else None
    logging_dir = parser.parse_args().logging_dir[0]
    config_dir = parser.parse_args().config_dir[0]
    return proc_n, logging_dir, config_dir

if __name__ == '__main__':
    proc_n, logging_dir, config_dir = get_arguments()
    try:
        runtime_config = load_runtime_config(
            config_path=config_dir,
            logging_dir=logging_dir,
            proc_n_override=proc_n,
        )
    except ConfigValidationError as exc:
        print("Invalid trade_core runtime configuration:", file=sys.stderr)
        for error in exc.errors:
            print(f"- {error}", file=sys.stderr)
        raise SystemExit(1)
    except Exception:
        print("Failed to load trade_core runtime configuration.", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        raise SystemExit(1)

    from etc.acw_api import AcwApi
    from etc.command_handler import CommandHandler
    from trade_core import InitCore
    
    # Starting message
    acw_api = AcwApi(
        runtime_config.acw_api_url,
        runtime_config.node,
        runtime_config.prod,
    )
    acw_api.create_message_thread(
        runtime_config.admin_telegram_id,
        f"Node:{runtime_config.node} is starting with {runtime_config.proc_n} processes..",
        f"Node:{runtime_config.node} is starting with {runtime_config.proc_n} processes..",
    )

    # Initiate Kimp core (Websocket engine)
    core = InitCore(
        runtime_config.logging_dir,
        runtime_config.proc_n,
        runtime_config.node,
        runtime_config.admin_telegram_id,
        acw_api,
        runtime_config.exchange_api_key_dict,
        runtime_config.postgres_db_dict,
        runtime_config.mongodb_dict,
        runtime_config.redis_dict,
    )

    time.sleep(5)
    
    # Start command handler loop
    command_handler = CommandHandler(
        runtime_config.acw_api_url,
        runtime_config.node,
        runtime_config.prod,
        runtime_config.admin_telegram_id,
        core,
        runtime_config.logging_dir,
    )
    command_handler.fetch_command_loop()
