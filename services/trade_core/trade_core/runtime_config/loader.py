from __future__ import annotations

import os

from dotenv import load_dotenv

from .schema import (
    ExchangeReadOnlyConfig,
    MongoConfig,
    PostgresConfig,
    RedisConfig,
    TradeCoreRuntimeConfig,
)
from .validators import (
    ConfigValidationError,
    ensure_valid,
    optional_string,
    parse_bool,
    parse_int,
    parse_int_list,
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
    }


def load_runtime_config(
    config_path: str,
    logging_dir: str,
    proc_n_override: int | None = None,
) -> TradeCoreRuntimeConfig:
    errors: list[str] = []

    validate_config_path(config_path, errors)
    ensure_valid(errors)
    load_dotenv(config_path)

    prod = parse_bool("PROD", os.getenv("PROD", "false"), errors)
    node = require_string("NODE", os.getenv("NODE"), errors)
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
    postgres = PostgresConfig(
        host=require_string("POSTGRES_HOST", os.getenv("POSTGRES_HOST"), errors),
        port=parse_int("POSTGRES_PORT", os.getenv("POSTGRES_PORT"), errors, minimum=1) or 5432,
        user=require_string("POSTGRES_USER", os.getenv("POSTGRES_USER"), errors),
        passwd=require_string("POSTGRES_PASS", os.getenv("POSTGRES_PASS"), errors),
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

    encryption_key = optional_string(os.getenv("ENCRYPTION_KEY"))
    openai_api_key = optional_string(os.getenv("OPENAI_API_KEY"))

    if not logging_dir:
        errors.append("logging_dir is empty")
    else:
        os.makedirs(logging_dir, exist_ok=True)

    ensure_valid(errors)

    return TradeCoreRuntimeConfig(
        prod=prod,
        node=node,
        proc_n=proc_n or 1,
        logging_dir=logging_dir,
        config_path=config_path,
        admin_telegram_id=admin_telegram_id or 1,
        staff_telegram_id_list=staff_telegram_id_list,
        acw_api_url=acw_api_url,
        encryption_key=encryption_key,
        openai_api_key=openai_api_key,
        mongodb=mongodb,
        redis=redis,
        postgres=postgres,
        exchange_api_key_dict=_build_exchange_api_key_dict(),
    )


__all__ = [
    "ConfigValidationError",
    "load_runtime_config",
]
