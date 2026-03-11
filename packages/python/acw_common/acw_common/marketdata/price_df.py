import _pickle as pickle
import traceback
import threading

import numpy as np
import pandas as pd


MARKET_STATE_VERSION_PREFIX = "MARKET_STATE_VERSION"

_PRICE_DF_CACHE = {}
_PRICE_DF_CACHE_LOCK = threading.RLock()


def _decode_version(raw_value):
    if raw_value is None:
        return None
    if isinstance(raw_value, bytes):
        return raw_value.decode("utf-8")
    return str(raw_value)


def _read_version(redis_client, key_name):
    return _decode_version(redis_client.get_data(key_name))


def get_market_data_signature(redis_client, market_code):
    signature = {
        "market_code": market_code,
        "market_state_version": _read_version(
            redis_client,
            f"{MARKET_STATE_VERSION_PREFIX}|{market_code}",
        )
    }
    return signature


def _signature_has_versions(signature):
    return signature.get("market_state_version") is not None


def _get_cached_price_df(cache_key, signature):
    with _PRICE_DF_CACHE_LOCK:
        cached_entry = _PRICE_DF_CACHE.get(cache_key)
        if not cached_entry:
            return None
        if cached_entry["signature"] != signature:
            return None
        return cached_entry["df"].copy()


def _store_cached_price_df(cache_key, signature, df):
    with _PRICE_DF_CACHE_LOCK:
        _PRICE_DF_CACHE[cache_key] = {
            "signature": signature,
            "df": df.copy(),
        }


def get_binance_price_df(redis_client, market_type):
    binance_ticker_df = pd.DataFrame(
        redis_client.get_all_exchange_stream_data("ticker", f"BINANCE_{market_type}")
    ).T.reset_index(drop=True)[["s", "P", "c", "v", "q"]]
    binance_ticker_df.rename(columns={"q": "atp24h", "P": "scr", "c": "tp"}, inplace=True)
    binance_bookticker_df = pd.DataFrame(
        redis_client.get_all_exchange_stream_data("orderbook", f"BINANCE_{market_type}")
    ).T.reset_index(drop=True)[["s", "b", "a"]]
    binance_bookticker_df.rename(columns={"b": "bp", "a": "ap"}, inplace=True)
    binance_merged_df = pd.merge(binance_ticker_df, binance_bookticker_df, on="s", how="inner")
    binance_merged_df[["scr", "tp", "atp24h", "ap", "bp"]] = binance_merged_df[
        ["scr", "tp", "atp24h", "ap", "bp"]
    ].astype(float)
    binance_info_df = pickle.loads(
        redis_client.get_data(f"binance_{market_type.lower()}_info_df")
    )[["symbol", "base_asset", "quote_asset"]]
    binance_merged_df = binance_merged_df.merge(
        binance_info_df, left_on="s", right_on="symbol", how="inner"
    )
    binance_merged_df.drop(["symbol", "s"], axis=1, inplace=True)
    return binance_merged_df


def get_bithumb_price_df(redis_client):
    orderbook_df = pd.DataFrame(
        redis_client.get_all_exchange_stream_data("orderbook", "BITHUMB_SPOT")
    ).T.reset_index()
    ticker_df = pd.DataFrame(
        redis_client.get_all_exchange_stream_data("ticker", "BITHUMB_SPOT")
    ).T.reset_index()

    orderbook_df = orderbook_df[orderbook_df["bids"].apply(lambda x: len(x) > 0)]
    if orderbook_df.empty:
        return pd.DataFrame(
            columns=[
                "symbol",
                "best_ask",
                "best_bid",
                "tp",
                "scr",
                "atp24h",
                "base_asset",
                "quote_asset",
                "ap",
                "bp",
            ]
        )

    orderbook_df["best_ask"] = orderbook_df["asks"].apply(lambda x: x[0][0])
    orderbook_df["best_bid"] = orderbook_df["bids"].apply(lambda x: x[0][0])

    merged_df = orderbook_df.merge(
        ticker_df[["symbol", "closePrice", "chgRate", "value"]],
        on="symbol",
        how="inner",
    )
    merged_df[["base_asset", "quote_asset"]] = merged_df["symbol"].str.split(
        "_", expand=True
    )
    merged_df = merged_df.rename(
        columns={
            "value": "atp24h",
            "chgRate": "scr",
            "closePrice": "tp",
            "best_ask": "ap",
            "best_bid": "bp",
        }
    )
    merged_df[["scr", "atp24h", "tp", "ap", "bp"]] = merged_df[
        ["scr", "atp24h", "tp", "ap", "bp"]
    ].astype(float)
    return merged_df


def get_bybit_price_df(redis_client, market_type):
    ticker_df = pd.DataFrame(
        redis_client.get_all_exchange_stream_data("ticker", f"BYBIT_{market_type}")
    ).T.reset_index()
    orderbook_df = pd.DataFrame(
        redis_client.get_all_exchange_stream_data("orderbook", f"BYBIT_{market_type}")
    ).T.reset_index()
    merged_df = ticker_df.merge(orderbook_df, left_on="symbol", right_on="s", how="inner")
    bybit_info_df = pickle.loads(redis_client.get_data(f"bybit_{market_type.lower()}_info_df"))[
        ["symbol", "base_asset", "quote_asset"]
    ]
    merged_df = merged_df.merge(bybit_info_df, on="symbol", how="inner")
    merged_df["b"] = merged_df["b"].apply(lambda x: x[0][0])
    merged_df["a"] = merged_df["a"].apply(lambda x: x[0][0])
    merged_df["price24hPcnt"] = merged_df["price24hPcnt"].astype(float) * 100
    if market_type == "COIN_M":
        merged_df = merged_df.rename(
            columns={
                "lastPrice": "tp",
                "a": "ap",
                "b": "bp",
                "price24hPcnt": "scr",
                "volume24h": "atp24h",
            }
        )
    else:
        merged_df = merged_df.rename(
            columns={
                "lastPrice": "tp",
                "a": "ap",
                "b": "bp",
                "price24hPcnt": "scr",
                "turnover24h": "atp24h",
            }
        )
    merged_df[["tp", "ap", "bp", "scr", "atp24h"]] = merged_df[
        ["tp", "ap", "bp", "scr", "atp24h"]
    ].astype(float)
    return merged_df[["symbol", "base_asset", "quote_asset", "tp", "bp", "ap", "scr", "atp24h"]]


def get_okx_price_df(redis_client, market_type):
    ticker_df = pd.DataFrame(
        redis_client.get_all_exchange_stream_data("ticker", f"OKX_{market_type}")
    ).T
    ticker_df["base_asset"] = ticker_df["instId"].apply(lambda x: x.split("-")[0])
    ticker_df["quote_asset"] = ticker_df["instId"].apply(lambda x: x.split("-")[1])
    ticker_df = ticker_df.rename(
        columns={"last": "tp", "askPx": "ap", "bidPx": "bp", "volCcy24h": "atp24h"}
    )
    ticker_df[["tp", "ap", "bp", "open24h", "atp24h"]] = ticker_df[
        ["tp", "ap", "bp", "open24h", "atp24h"]
    ].astype(float)
    ticker_df["atp24h"] = ticker_df.apply(
        lambda x: x["tp"] * x["atp24h"] if x["instType"] != "SPOT" else x["atp24h"],
        axis=1,
    )
    ticker_df["scr"] = (ticker_df["tp"] - ticker_df["open24h"]) / ticker_df["open24h"] * 100
    return ticker_df[["instId", "base_asset", "quote_asset", "tp", "ap", "bp", "scr", "atp24h"]]


def get_upbit_price_df(redis_client):
    upbit_ticker_df = pd.DataFrame(
        redis_client.get_all_exchange_stream_data("ticker", "UPBIT_SPOT")
    ).T.reset_index()[["index", "tp", "scr", "atp24h", "h52wp", "l52wp", "ms", "mw", "tms"]]
    upbit_orderbook_df = pd.DataFrame(
        redis_client.get_all_exchange_stream_data("orderbook", "UPBIT_SPOT")
    ).T.reset_index(drop=True)[["cd", "tms", "obu"]]
    upbit_orderbook_df["ap"] = upbit_orderbook_df["obu"].apply(lambda x: x[0]["ap"])
    upbit_orderbook_df["bp"] = upbit_orderbook_df["obu"].apply(lambda x: x[0]["bp"])
    upbit_orderbook_df.drop("obu", axis=1, inplace=True)
    upbit_merged_df = pd.merge(
        upbit_ticker_df, upbit_orderbook_df, left_on="index", right_on="cd", how="inner"
    )
    upbit_merged_df = upbit_merged_df.dropna(subset=["tp", "ap", "bp"])
    upbit_merged_df["base_asset"] = upbit_merged_df["index"].apply(lambda x: x.split("-")[1])
    upbit_merged_df["quote_asset"] = upbit_merged_df["index"].apply(lambda x: x.split("-")[0])
    upbit_merged_df.drop("index", axis=1, inplace=True)
    upbit_merged_df[["scr", "atp24h", "h52wp", "l52wp", "ap", "bp"]] = upbit_merged_df[
        ["scr", "atp24h", "h52wp", "l52wp", "ap", "bp"]
    ].astype(float)
    upbit_merged_df["scr"] = upbit_merged_df["scr"] * 100
    return upbit_merged_df


def get_coinone_price_df(redis_client):
    ticker_data = redis_client.get_all_exchange_stream_data("ticker", "COINONE_SPOT")
    orderbook_data = redis_client.get_all_exchange_stream_data("orderbook", "COINONE_SPOT")

    if not ticker_data or not orderbook_data:
        return pd.DataFrame(
            columns=["symbol", "base_asset", "quote_asset", "tp", "bp", "ap", "scr", "atp24h"]
        )

    ticker_df = pd.DataFrame(ticker_data).T.reset_index(drop=True)
    orderbook_df = pd.DataFrame(orderbook_data).T.reset_index(drop=True)

    ticker_df = ticker_df[["symbol", "lastPrice", "atp24h", "openPrice"]].copy()
    ticker_df = ticker_df.rename(columns={"lastPrice": "tp"})
    ticker_df[["tp", "atp24h", "openPrice"]] = ticker_df[
        ["tp", "atp24h", "openPrice"]
    ].astype(float)
    ticker_df["scr"] = ((ticker_df["tp"] - ticker_df["openPrice"]) / ticker_df["openPrice"]) * 100
    ticker_df.drop("openPrice", axis=1, inplace=True)

    def extract_best_ask(order_list):
        if not order_list:
            return np.nan
        prices = []
        for order in order_list:
            try:
                if isinstance(order, dict):
                    price = float(order.get("price", 0))
                elif isinstance(order, (list, tuple)):
                    price = float(order[0])
                else:
                    continue
            except (TypeError, ValueError):
                continue
            if price > 0:
                prices.append(price)
        return min(prices) if prices else np.nan

    def extract_best_bid(order_list):
        if not order_list:
            return np.nan
        try:
            first_order = order_list[0]
            if isinstance(first_order, dict):
                price = float(first_order.get("price", 0))
            elif isinstance(first_order, (list, tuple)):
                price = float(first_order[0])
            else:
                return np.nan
        except (TypeError, ValueError):
            return np.nan
        return price if price > 0 else np.nan

    orderbook_df["ap"] = orderbook_df["asks"].apply(extract_best_ask)
    orderbook_df["bp"] = orderbook_df["bids"].apply(extract_best_bid)
    orderbook_df = orderbook_df[["symbol", "ap", "bp"]]

    merged_df = ticker_df.merge(orderbook_df, on="symbol", how="inner")
    merged_df = merged_df.dropna(subset=["tp", "ap", "bp"])
    merged_df[["base_asset", "quote_asset"]] = merged_df["symbol"].str.split("_", expand=True)
    return merged_df[["symbol", "base_asset", "quote_asset", "tp", "bp", "ap", "scr", "atp24h"]]


def get_gate_price_df(redis_client, market_type):
    ticker_data = redis_client.get_all_exchange_stream_data("ticker", f"GATE_{market_type}")
    orderbook_data = redis_client.get_all_exchange_stream_data("orderbook", f"GATE_{market_type}")

    if not ticker_data or not orderbook_data:
        return pd.DataFrame(
            columns=["symbol", "base_asset", "quote_asset", "tp", "bp", "ap", "scr", "atp24h"]
        )

    ticker_df = pd.DataFrame(ticker_data).T.reset_index(drop=True)
    orderbook_df = pd.DataFrame(orderbook_data).T.reset_index(drop=True)
    ticker_df = ticker_df[["s", "c", "P", "q"]].copy().rename(
        columns={"c": "tp", "P": "scr", "q": "atp24h"}
    )
    orderbook_df = orderbook_df[["s", "b", "a"]].copy().rename(
        columns={"b": "bp", "a": "ap"}
    )
    merged_df = ticker_df.merge(orderbook_df, on="s", how="inner")
    merged_df[["tp", "scr", "atp24h", "bp", "ap"]] = merged_df[
        ["tp", "scr", "atp24h", "bp", "ap"]
    ].astype(float)
    gate_info_df = pickle.loads(redis_client.get_data(f"gate_{market_type.lower()}_info_df"))[
        ["symbol", "base_asset", "quote_asset"]
    ]
    merged_df = merged_df.merge(gate_info_df, left_on="s", right_on="symbol", how="inner")
    merged_df.drop(["symbol", "s"], axis=1, inplace=True)
    return merged_df


def get_hyperliquid_price_df(redis_client, market_type):
    ticker_data = redis_client.get_all_exchange_stream_data(
        "ticker", f"HYPERLIQUID_{market_type}"
    )
    orderbook_data = redis_client.get_all_exchange_stream_data(
        "orderbook", f"HYPERLIQUID_{market_type}"
    )

    if not ticker_data or not orderbook_data:
        return pd.DataFrame(
            columns=["symbol", "base_asset", "quote_asset", "tp", "bp", "ap", "scr", "atp24h"]
        )

    ticker_df = pd.DataFrame(ticker_data).T.reset_index(drop=True)
    orderbook_df = pd.DataFrame(orderbook_data).T.reset_index(drop=True)
    ticker_df = ticker_df[["s", "c"]].copy().rename(columns={"c": "tp"})
    orderbook_df = orderbook_df[["s", "b", "a"]].copy().rename(
        columns={"b": "bp", "a": "ap"}
    )
    merged_df = ticker_df.merge(orderbook_df, on="s", how="inner")
    merged_df[["tp", "bp", "ap"]] = merged_df[["tp", "bp", "ap"]].astype(float)
    merged_df = merged_df[(merged_df["tp"] > 0) & (merged_df["bp"] > 0) & (merged_df["ap"] > 0)]

    if merged_df.empty:
        return pd.DataFrame(
            columns=["base_asset", "quote_asset", "tp", "bp", "ap", "scr", "atp24h"]
        )

    try:
        hyperliquid_ticker_cache = redis_client.get_data(
            f"hyperliquid_{market_type.lower()}_ticker_df"
        )
        if hyperliquid_ticker_cache:
            rest_ticker_df = pickle.loads(hyperliquid_ticker_cache)
            if not rest_ticker_df.empty and "atp24h" in rest_ticker_df.columns:
                rest_cols = rest_ticker_df[["symbol", "atp24h", "priceChangePercent"]].copy()
                rest_cols = rest_cols.rename(columns={"priceChangePercent": "scr"})
                merged_df = merged_df.merge(rest_cols, left_on="s", right_on="symbol", how="left")
                merged_df.drop("symbol", axis=1, inplace=True)
            else:
                merged_df["atp24h"] = 0.0
                merged_df["scr"] = 0.0
        else:
            merged_df["atp24h"] = 0.0
            merged_df["scr"] = 0.0
    except Exception:
        merged_df["atp24h"] = 0.0
        merged_df["scr"] = 0.0

    try:
        hyperliquid_info_df = pickle.loads(
            redis_client.get_data(f"hyperliquid_{market_type.lower()}_info_df")
        )
        if hyperliquid_info_df is not None and not hyperliquid_info_df.empty:
            info_cols = hyperliquid_info_df[["symbol", "base_asset", "quote_asset"]]
            merged_df = merged_df.merge(info_cols, left_on="s", right_on="symbol", how="inner")
            merged_df.drop(["symbol", "s"], axis=1, inplace=True)
        else:
            merged_df["base_asset"] = merged_df["s"].apply(lambda x: x.split("_")[0] if "_" in x else x)
            merged_df["quote_asset"] = "USDC"
            merged_df["symbol"] = merged_df["base_asset"] + "_USDC"
            merged_df.drop("s", axis=1, inplace=True)
    except Exception:
        merged_df["base_asset"] = merged_df["s"].apply(lambda x: x.split("_")[0] if "_" in x else x)
        merged_df["quote_asset"] = "USDC"
        merged_df["symbol"] = merged_df["base_asset"] + "_USDC"
        merged_df.drop("s", axis=1, inplace=True)

    merged_df[["tp", "bp", "ap", "atp24h", "scr"]] = merged_df[
        ["tp", "bp", "ap", "atp24h", "scr"]
    ].astype(float)
    return merged_df[["base_asset", "quote_asset", "tp", "bp", "ap", "scr", "atp24h"]]


EXCHANGE_HANDLERS = {
    "BINANCE": get_binance_price_df,
    "BITHUMB": get_bithumb_price_df,
    "BYBIT": get_bybit_price_df,
    "OKX": get_okx_price_df,
    "UPBIT": get_upbit_price_df,
    "GATE": get_gate_price_df,
    "COINONE": get_coinone_price_df,
    "HYPERLIQUID": get_hyperliquid_price_df,
}


def get_price_df(redis_client, market_code):
    exchange = market_code.split("_")[0].upper()
    market_type = "_".join(market_code.split("_")[1:]).upper()

    handler = EXCHANGE_HANDLERS.get(exchange)
    if handler is None:
        raise ValueError(f"get_price_df|exchange: {exchange} is not supported!")

    signature_before = get_market_data_signature(redis_client, market_code)
    if _signature_has_versions(signature_before):
        cached_df = _get_cached_price_df(market_code, signature_before)
        if cached_df is not None:
            return cached_df

    if exchange in {"BINANCE", "BYBIT", "OKX", "GATE", "HYPERLIQUID"}:
        df = handler(redis_client, market_type)
    else:
        df = handler(redis_client)

    signature_after = get_market_data_signature(redis_client, market_code)
    if (
        _signature_has_versions(signature_before)
        and signature_before != signature_after
    ):
        if exchange in {"BINANCE", "BYBIT", "OKX", "GATE", "HYPERLIQUID"}:
            df = handler(redis_client, market_type)
        else:
            df = handler(redis_client)
        signature_after = get_market_data_signature(redis_client, market_code)

    if _signature_has_versions(signature_after):
        _store_cached_price_df(market_code, signature_after, df)

    return df
