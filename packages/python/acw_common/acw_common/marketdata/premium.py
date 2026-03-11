import pandas as pd
import traceback

from .price_df import get_price_df


PREMIUM_COLUMNS = [
    "tp_premium",
    "LS_premium",
    "SL_premium",
    "LS_SL_spread",
    "base_asset",
    "quote_asset",
    "tp",
    "ap",
    "bp",
    "scr",
    "atp24h",
    "converted_tp",
    "converted_ap",
    "converted_bp",
    "dollar",
]


def empty_premium_df():
    return pd.DataFrame(columns=PREMIUM_COLUMNS)


def build_premium_df_from_market_snapshots(
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
    try:
        origin_filtered = origin_market_df[
            origin_market_df["quote_asset"] == quote_asset_one
        ][["base_asset", "tp", "ap", "bp"]]
        target_filtered = target_market_df[
            target_market_df["quote_asset"] == quote_asset_two
        ][["base_asset", "quote_asset", "tp", "ap", "bp", "scr", "atp24h"]]

        if origin_filtered.empty or target_filtered.empty:
            if logger:
                logger.warning(
                    f"get_premium_df|Empty price data: origin={len(origin_filtered)}, target={len(target_filtered)}"
                )
            return empty_premium_df()

        merged_df = origin_filtered.merge(
            target_filtered,
            on="base_asset",
            how="inner",
            suffixes=("_origin", "_target"),
        )
        if merged_df.empty:
            if logger and target_market_code and origin_market_code:
                logger.warning(
                    f"get_premium_df|No shared symbols between {origin_market_code} and {target_market_code}"
                )
            return empty_premium_df()

        converted_prices = merged_df[["tp_origin", "ap_origin", "bp_origin"]].values * convert_rate
        valid_mask = (
            (converted_prices[:, 0] > 0)
            & (converted_prices[:, 1] > 0)
            & (converted_prices[:, 2] > 0)
        )
        merged_df = merged_df[valid_mask].reset_index(drop=True)
        converted_prices = converted_prices[valid_mask]

        if merged_df.empty:
            if logger:
                logger.warning("get_premium_df|No valid price data after filtering zeros")
            return empty_premium_df()

        target_prices = merged_df[["tp_target", "ap_target", "bp_target"]].values
        premium_values = (
            target_prices
            - converted_prices[:, [0, 2, 1]]
        ) / converted_prices[:, [0, 2, 1]]

        premium_df = pd.DataFrame(
            premium_values,
            columns=["tp_premium", "LS_premium", "SL_premium"],
        )
        premium_df["LS_SL_spread"] = premium_df["LS_premium"] - premium_df["SL_premium"]
        premium_df[["base_asset", "quote_asset", "tp", "ap", "bp", "scr", "atp24h"]] = merged_df[
            ["base_asset", "quote_asset", "tp_target", "ap_target", "bp_target", "scr", "atp24h"]
        ]
        premium_df[["converted_tp", "converted_ap", "converted_bp"]] = converted_prices
        premium_df.loc[:, ["tp_premium", "LS_premium", "SL_premium", "LS_SL_spread"]] = (
            premium_df[["tp_premium", "LS_premium", "SL_premium", "LS_SL_spread"]] * 100
        )
        if sort_by_atp24h:
            premium_df = premium_df.sort_values("atp24h", ascending=False).reset_index(drop=True)
        premium_df["dollar"] = dollar_price
        return premium_df
    except Exception as exc:
        if logger:
            logger.error(
                f"get_premium_df|Exception occured! Error: {exc}, traceback: {traceback.format_exc()}"
            )
        raise


def build_premium_df(
    redis_client,
    convert_rate_dict,
    target_market_code,
    origin_market_code,
    logger,
    get_dollar_dict_fn,
    get_price_df_fn=get_price_df,
):
    try:
        origin_market = origin_market_code.split("/")[0]
        quote_asset_one = origin_market_code.split("/")[1]
        target_market = target_market_code.split("/")[0]
        quote_asset_two = target_market_code.split("/")[1]

        origin_market_df = get_price_df_fn(redis_client, origin_market)
        origin_market_df = origin_market_df[origin_market_df["quote_asset"] == quote_asset_one]
        target_market_df = get_price_df_fn(redis_client, target_market)
        target_market_df = target_market_df[target_market_df["quote_asset"] == quote_asset_two]
        convert_rate = convert_rate_dict[f"{target_market_code}:{origin_market_code}"]
        dollar_price = get_dollar_dict_fn(redis_client)["price"]
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
        )
    except Exception as exc:
        logger.error(
            f"get_premium_df|Exception occured! Error: {exc}, traceback: {traceback.format_exc()}"
        )
        raise
