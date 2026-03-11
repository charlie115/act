from _acw_common import ensure_acw_common_on_path

ensure_acw_common_on_path()

from acw_common.marketdata.premium import build_premium_df

from standalone_func.get_dollar_dict import get_dollar_dict
from standalone_func.price_df_generator import get_price_df


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
