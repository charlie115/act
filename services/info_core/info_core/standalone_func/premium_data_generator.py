from _acw_common import ensure_acw_common_on_path

ensure_acw_common_on_path()

import datetime
import _pickle as pickle

import pandas as pd

from acw_common.marketdata.premium import (
    build_premium_df,
    build_premium_df_from_market_snapshots,
)

from standalone_func.get_dollar_dict import get_dollar_dict
from standalone_func.price_df_generator import get_market_data_signature, get_price_df


PREMIUM_REDIS_PREFIX = "premium"
CONVERT_RATE_VERSION_PREFIX = "CONVERT_RATE_VERSION"


def _decode_version(raw_value):
    if raw_value is None:
        return None
    if isinstance(raw_value, bytes):
        return raw_value.decode("utf-8")
    return str(raw_value)


def get_convert_rate_version(redis_client, market_code_combination):
    return _decode_version(
        redis_client.get_data(
            f"{CONVERT_RATE_VERSION_PREFIX}|{market_code_combination}",
        )
    )


def _to_market_state_code(market_code):
    return market_code.split("/")[0]


def build_premium_cache_metadata(
    redis_client,
    market_code_combination,
    target_market_code,
    origin_market_code,
):
    return {
        "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f"),
        "market_code_combination": market_code_combination,
        "target_signature": get_market_data_signature(
            redis_client,
            _to_market_state_code(target_market_code),
        ),
        "origin_signature": get_market_data_signature(
            redis_client,
            _to_market_state_code(origin_market_code),
        ),
        "convert_rate_version": get_convert_rate_version(
            redis_client,
            market_code_combination,
        ),
    }


def _premium_cache_is_fresh(cache_payload, expected_metadata):
    if not cache_payload or not expected_metadata:
        return False
    cached_metadata = cache_payload.get("metadata")
    if not cached_metadata:
        return False
    return (
        cached_metadata.get("target_signature") == expected_metadata.get("target_signature")
        and cached_metadata.get("origin_signature") == expected_metadata.get("origin_signature")
        and cached_metadata.get("convert_rate_version") == expected_metadata.get("convert_rate_version")
    )


def get_premium_df(redis_client, convert_rate_dict, target_market_code, origin_market_code, logger):
    return build_premium_df(
        redis_client=redis_client,
        convert_rate_dict=convert_rate_dict,
        target_market_code=target_market_code,
        origin_market_code=origin_market_code,
        logger=logger,
        get_dollar_dict_fn=get_dollar_dict,
        get_price_df_fn=get_price_df,
    )


def get_premium_df_from_market_snapshots(
    origin_market_df,
    target_market_df,
    quote_asset_one,
    quote_asset_two,
    convert_rate,
    dollar_price,
    logger,
    target_market_code=None,
    origin_market_code=None,
    sort_by_atp24h=True,
):
    return build_premium_df_from_market_snapshots(
        origin_market_df=origin_market_df,
        target_market_df=target_market_df,
        quote_asset_one=quote_asset_one,
        quote_asset_two=quote_asset_two,
        convert_rate=convert_rate,
        dollar_price=dollar_price,
        logger=logger,
        target_market_code=target_market_code,
        origin_market_code=origin_market_code,
        sort_by_atp24h=sort_by_atp24h,
    )


def get_premium_cache_key(market_code_combination):
    return f"{PREMIUM_REDIS_PREFIX}|{market_code_combination}"


def store_premium_df(redis_client, market_code_combination, premium_df, metadata=None, ex=5):
    redis_client.set_data(
        get_premium_cache_key(market_code_combination),
        pickle.dumps(
            {
                "premium_df": premium_df,
                "metadata": metadata or {},
            }
        ),
        ex=ex,
    )


def get_cached_premium_df(redis_client, market_code_combination):
    cached = redis_client.get_data(get_premium_cache_key(market_code_combination))
    if not cached:
        return {"premium_df": pd.DataFrame(), "metadata": {}}
    cached_payload = pickle.loads(cached)
    if isinstance(cached_payload, pd.DataFrame):
        return {"premium_df": cached_payload, "metadata": {}}
    return cached_payload


def get_or_build_premium_df(
    redis_client,
    market_code_combination,
    logger,
    convert_rate_dict=None,
    target_market_code=None,
    origin_market_code=None,
):
    if not target_market_code or not origin_market_code:
        target_market_code, origin_market_code = market_code_combination.split(":")

    expected_metadata = build_premium_cache_metadata(
        redis_client,
        market_code_combination,
        target_market_code,
        origin_market_code,
    )
    cached_payload = get_cached_premium_df(redis_client, market_code_combination)
    cached_premium_df = cached_payload.get("premium_df", pd.DataFrame())
    if not cached_premium_df.empty and _premium_cache_is_fresh(cached_payload, expected_metadata):
        return cached_premium_df

    if not convert_rate_dict:
        return cached_premium_df

    premium_df = get_premium_df(
        redis_client,
        convert_rate_dict,
        target_market_code,
        origin_market_code,
        logger,
    )
    if not premium_df.empty:
        stored_metadata = build_premium_cache_metadata(
            redis_client,
            market_code_combination,
            target_market_code,
            origin_market_code,
        )
        store_premium_df(
            redis_client,
            market_code_combination,
            premium_df,
            metadata=stored_metadata,
            ex=5,
        )
    return premium_df
