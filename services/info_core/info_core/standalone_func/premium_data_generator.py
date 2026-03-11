from _acw_common import ensure_acw_common_on_path

ensure_acw_common_on_path()

import _pickle as pickle

import pandas as pd

from acw_common.marketdata.premium import build_premium_df

from standalone_func.get_dollar_dict import get_dollar_dict
from standalone_func.price_df_generator import get_price_df


PREMIUM_REDIS_PREFIX = "premium"


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


def get_premium_cache_key(market_code_combination):
    return f"{PREMIUM_REDIS_PREFIX}|{market_code_combination}"


def store_premium_df(redis_client, market_code_combination, premium_df, ex=5):
    redis_client.set_data(
        get_premium_cache_key(market_code_combination),
        pickle.dumps(premium_df),
        ex=ex,
    )


def get_cached_premium_df(redis_client, market_code_combination):
    cached = redis_client.get_data(get_premium_cache_key(market_code_combination))
    if not cached:
        return pd.DataFrame()
    return pickle.loads(cached)


def get_or_build_premium_df(
    redis_client,
    market_code_combination,
    logger,
    convert_rate_dict=None,
    target_market_code=None,
    origin_market_code=None,
):
    cached = get_cached_premium_df(redis_client, market_code_combination)
    if not cached.empty:
        return cached

    if not convert_rate_dict:
        return cached

    if not target_market_code or not origin_market_code:
        target_market_code, origin_market_code = market_code_combination.split(":")

    return get_premium_df(
        redis_client,
        convert_rate_dict,
        target_market_code,
        origin_market_code,
        logger,
    )
