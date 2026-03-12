from __future__ import annotations

import os

from dotenv import load_dotenv

from .schema import (
    ExchangeReadOnlyConfig,
    InfoCoreRuntimeConfig,
    MongoConfig,
    RedisConfig,
)
from .validators import (
    ConfigValidationError,
    ensure_valid,
    optional_string,
    parse_bool,
    parse_int,
    parse_int_list,
    parse_market_combination_list,
    require_string,
    validate_config_path,
    validate_url,
)


def _build_exchange_api_key_dict():
    def exchange_config(prefix: str, *, with_passphrase: bool = False):
        config = ExchangeReadOnlyConfig(
            api_key=optional_string(os.getenv(f"{prefix}_ACCESS_KEY")),
            secret_key=optional_string(os.getenv(f"{prefix}_SECRET_KEY")),
            passphrase=optional_string(os.getenv(f"{prefix}_PASSPHRASE"))
            if with_passphrase
            else None,
        )
        config_dict = {
            "api_key": config.api_key,
            "secret_key": config.secret_key,
        }
        if with_passphrase:
            config_dict["passphrase"] = config.passphrase
        return config_dict

    return {
        "binance_read_only": exchange_config("BINANCE"),
        "okx_read_only": exchange_config("OKX", with_passphrase=True),
        "upbit_read_only": exchange_config("UPBIT"),
        "bithumb_read_only": exchange_config("BITHUMB"),
        "bybit_read_only": exchange_config("BYBIT"),
        "gate_read_only": exchange_config("GATE"),
        "coinone_read_only": exchange_config("COINONE"),
    }


def load_runtime_config(
    config_path: str,
    logging_dir: str,
    proc_n_override: int | None = None,
) -> InfoCoreRuntimeConfig:
    errors: list[str] = []

    validate_config_path(config_path, errors)
    ensure_valid(errors)
    load_dotenv(config_path)

    prod = parse_bool("PROD", os.getenv("PROD", "false"), errors)
    node = require_string("NODE", os.getenv("NODE"), errors)
    master = parse_bool("MASTER", os.getenv("MASTER"), errors)
    raw_run_funding_updater = os.getenv("RUN_FUNDING_UPDATER")
    run_funding_updater = (
        master
        if raw_run_funding_updater is None
        else parse_bool("RUN_FUNDING_UPDATER", raw_run_funding_updater, errors)
    )
    raw_run_wallet_status_updater = os.getenv("RUN_WALLET_STATUS_UPDATER")
    run_wallet_status_updater = (
        master
        if raw_run_wallet_status_updater is None
        else parse_bool("RUN_WALLET_STATUS_UPDATER", raw_run_wallet_status_updater, errors)
    )

    raw_proc_n = str(proc_n_override) if proc_n_override is not None else os.getenv("PROC_N")
    proc_n = parse_int("PROC_N", raw_proc_n, errors, minimum=1)

    mongodb = MongoConfig(
        host=require_string("MONGODB_HOST", os.getenv("MONGODB_HOST"), errors),
        port=parse_int("MONGODB_PORT", os.getenv("MONGODB_PORT", "27017"), errors, minimum=1) or 27017,
        user=optional_string(os.getenv("MONGODB_USER")),
        passwd=optional_string(os.getenv("MONGODB_PASS")),
    )
    redis = RedisConfig(
        host=require_string("REDIS_HOST", os.getenv("REDIS_HOST"), errors),
        port=parse_int("REDIS_PORT", os.getenv("REDIS_PORT", "6379"), errors, minimum=1) or 6379,
        passwd=optional_string(os.getenv("REDIS_PASS")),
    )

    admin_telegram_id = parse_int(
        "ADMIN_TELEGRAM_ID",
        os.getenv("ADMIN_TELEGRAM_ID"),
        errors,
        minimum=1,
    )
    staff_telegram_id_list = parse_int_list(
        "STAFF_TELEGRAM_ID_LIST",
        os.getenv("STAFF_TELEGRAM_ID_LIST"),
        errors,
    )
    acw_api_url = validate_url("ACW_API_URL", os.getenv("ACW_API_URL"), errors)
    ai_api_key = optional_string(os.getenv("AIENGINE_API_KEY"))

    enabled_market_klines = parse_market_combination_list(
        "ENABLED_MARKET_KLINES",
        os.getenv("ENABLED_MARKET_KLINES"),
        errors,
        required=True,
    )
    enabled_arbitrage_markets = parse_market_combination_list(
        "ENABLED_ARBITRAGE_MARKETS",
        os.getenv("ENABLED_ARBITRAGE_MARKETS", os.getenv("ENALBED_ARBITRAGE_MARKETS")),
        errors,
        required=False,
    )

    if not logging_dir:
        errors.append("logging_dir is empty")
    else:
        os.makedirs(logging_dir, exist_ok=True)

    ensure_valid(errors)

    return InfoCoreRuntimeConfig(
        prod=prod,
        node=node,
        master=master,
        run_funding_updater=run_funding_updater,
        run_wallet_status_updater=run_wallet_status_updater,
        proc_n=proc_n or 1,
        logging_dir=logging_dir,
        config_path=config_path,
        admin_telegram_id=admin_telegram_id or 1,
        staff_telegram_id_list=staff_telegram_id_list,
        acw_api_url=acw_api_url,
        ai_api_key=ai_api_key,
        enabled_market_klines=enabled_market_klines,
        enabled_arbitrage_markets=enabled_arbitrage_markets,
        mongodb=mongodb,
        redis=redis,
        exchange_api_key_dict=_build_exchange_api_key_dict(),
    )


__all__ = [
    "ConfigValidationError",
    "load_runtime_config",
]
