from exchange_plugin.okx_plug import InitOkxAdaptor
from exchange_plugin.upbit_plug import InitUpbitAdaptor
from exchange_plugin.binance_plug import InitBinanceAdaptor
from exchange_plugin.bithumb_plug import InitBithumbAdaptor
from exchange_plugin.bybit_plug import InitBybitAdaptor
from exchange_plugin.gate_plug import InitGateAdaptor
from exchange_plugin.coinone_plug import InitCoinoneAdaptor
from exchange_plugin.hyperliquid_plug import InitHyperliquidAdaptor


def build_exchange_adaptors(exchange_api_key_dict, logging_dir):
    return {
        "BINANCE": InitBinanceAdaptor(
            exchange_api_key_dict["binance_read_only"]["api_key"],
            exchange_api_key_dict["binance_read_only"]["secret_key"],
            logging_dir,
        ),
        "OKX": InitOkxAdaptor(
            exchange_api_key_dict["okx_read_only"]["api_key"],
            exchange_api_key_dict["okx_read_only"]["secret_key"],
            exchange_api_key_dict["okx_read_only"]["passphrase"],
            logging_dir=logging_dir,
        ),
        "UPBIT": InitUpbitAdaptor(
            exchange_api_key_dict["upbit_read_only"]["api_key"],
            exchange_api_key_dict["upbit_read_only"]["secret_key"],
            logging_dir,
        ),
        "BITHUMB": InitBithumbAdaptor(logging_dir=logging_dir),
        "BYBIT": InitBybitAdaptor(
            exchange_api_key_dict["bybit_read_only"]["api_key"],
            exchange_api_key_dict["bybit_read_only"]["secret_key"],
            logging_dir,
        ),
        "GATE": InitGateAdaptor(
            exchange_api_key_dict.get("gate_read_only", {}).get("api_key"),
            exchange_api_key_dict.get("gate_read_only", {}).get("secret_key"),
            logging_dir,
        ),
        "COINONE": InitCoinoneAdaptor(
            exchange_api_key_dict.get("coinone_read_only", {}).get("api_key"),
            exchange_api_key_dict.get("coinone_read_only", {}).get("secret_key"),
            logging_dir,
        ),
        "HYPERLIQUID": InitHyperliquidAdaptor(logging_dir),
    }


def funding_exchange_targets(adaptors):
    return [
        ("BINANCE", adaptors["BINANCE"], 60),
        ("OKX", adaptors["OKX"], 180),
        ("BYBIT", adaptors["BYBIT"], 60),
        ("GATE", adaptors["GATE"], 60),
        ("HYPERLIQUID", adaptors["HYPERLIQUID"], 60),
    ]


def _has_credentials(exchange_api_key_dict, prefix, *, require_passphrase=False):
    config = exchange_api_key_dict.get(prefix, {})
    if not config.get("api_key") or not config.get("secret_key"):
        return False
    if require_passphrase and not config.get("passphrase"):
        return False
    return True


def wallet_status_exchange_targets(adaptors, exchange_api_key_dict):
    targets = []

    if _has_credentials(exchange_api_key_dict, "upbit_read_only"):
        targets.append(("UPBIT", adaptors["UPBIT"], 60))
    if _has_credentials(exchange_api_key_dict, "binance_read_only"):
        targets.append(("BINANCE", adaptors["BINANCE"], 60))
    if _has_credentials(exchange_api_key_dict, "okx_read_only", require_passphrase=True):
        targets.append(("OKX", adaptors["OKX"], 60))

    # Public wallet/network status sources
    targets.append(("BITHUMB", adaptors["BITHUMB"], 60))

    if _has_credentials(exchange_api_key_dict, "bybit_read_only"):
        targets.append(("BYBIT", adaptors["BYBIT"], 60))

    targets.append(("COINONE", adaptors["COINONE"], 60))

    return targets


def has_wallet_status_targets(exchange_api_key_dict):
    # Bithumb and Coinone use public wallet/network status sources in the current runtime.
    return True
