from etc.redis_connector.redis_helper import RedisHelper
import pandas as pd
import json
import traceback
from loggers.logger import InfoCoreLogger
from standalone_func.get_dollar_dict import get_dollar_dict
from standalone_func.price_df_generator import get_price_df

def get_premium_df(redis_client, convert_rate_dict, target_market_code, origin_market_code, logger):
    try:
        # POSSIBLE quote_assets: USDT, BUSD, BTC, KRW
        origin_market = origin_market_code.split('/')[0]
        quote_asset_one = origin_market_code.split('/')[1]
        target_market = target_market_code.split('/')[0]
        quote_asset_two = target_market_code.split('/')[1]

        origin_market_df = get_price_df(redis_client, origin_market)
        origin_market_df = origin_market_df[origin_market_df['quote_asset'] == quote_asset_one]
        target_market_df = get_price_df(redis_client, target_market)
        target_market_df = target_market_df[target_market_df['quote_asset'] == quote_asset_two]

        # Check for empty DataFrames
        if origin_market_df.empty or target_market_df.empty:
            logger.warning(f"get_premium_df|Empty price data: origin={len(origin_market_df)}, target={len(target_market_df)}")
            return pd.DataFrame(columns=['tp_premium', 'LS_premium', 'SL_premium', 'LS_SL_spread', 'base_asset', 'quote_asset', 'tp', 'ap', 'bp', 'scr', 'atp24h', 'converted_tp', 'converted_ap', 'converted_bp', 'dollar'])

        shared_base_asset_list = list(set(origin_market_df['base_asset'].values).intersection(set(target_market_df['base_asset'].values)))

        # Check for no shared symbols
        if not shared_base_asset_list:
            logger.warning(f"get_premium_df|No shared symbols between {origin_market_code} and {target_market_code}")
            return pd.DataFrame(columns=['tp_premium', 'LS_premium', 'SL_premium', 'LS_SL_spread', 'base_asset', 'quote_asset', 'tp', 'ap', 'bp', 'scr', 'atp24h', 'converted_tp', 'converted_ap', 'converted_bp', 'dollar'])

        origin_market_df = origin_market_df[origin_market_df['base_asset'].isin(shared_base_asset_list)].sort_values('base_asset').reset_index(drop=True)
        target_market_df = target_market_df[target_market_df['base_asset'].isin(shared_base_asset_list)].sort_values('base_asset').reset_index(drop=True)

        convert_rate = convert_rate_dict[f"{target_market_code}:{origin_market_code}"]
        origin_market_df[['converted_tp','converted_ap','converted_bp']] = origin_market_df[['tp','ap','bp']] * convert_rate

        # Filter out rows with zero prices to avoid division by zero
        valid_mask = (origin_market_df['converted_tp'] > 0) & (origin_market_df['converted_ap'] > 0) & (origin_market_df['converted_bp'] > 0)
        origin_market_df = origin_market_df[valid_mask].reset_index(drop=True)
        target_market_df = target_market_df[valid_mask].reset_index(drop=True)

        if origin_market_df.empty:
            logger.warning(f"get_premium_df|No valid price data after filtering zeros")
            return pd.DataFrame(columns=['tp_premium', 'LS_premium', 'SL_premium', 'LS_SL_spread', 'base_asset', 'quote_asset', 'tp', 'ap', 'bp', 'scr', 'atp24h', 'converted_tp', 'converted_ap', 'converted_bp', 'dollar'])

        # divide by target_market_df[['tp','ap','bp']]
        premium_df = pd.DataFrame((target_market_df[['tp','ap','bp']].values - origin_market_df[['converted_tp','converted_bp','converted_ap']].values)/
                                origin_market_df[['converted_tp','converted_bp','converted_ap']].values, columns=['tp_premium','LS_premium','SL_premium'])
        premium_df['LS_SL_spread'] = premium_df['LS_premium'] - premium_df['SL_premium']
        premium_df[['base_asset','quote_asset','tp','ap','bp','scr','atp24h']] = target_market_df[['base_asset','quote_asset','tp','ap','bp','scr','atp24h']]
        premium_df[['converted_tp','converted_ap','converted_bp']] = origin_market_df[['converted_tp','converted_ap', 'converted_bp']]
        premium_df.loc[:, ['tp_premium','LS_premium','SL_premium','LS_SL_spread']] = premium_df[['tp_premium','LS_premium','SL_premium','LS_SL_spread']] * 100
        premium_df = premium_df.sort_values('atp24h', ascending=False).reset_index(drop=True)
        premium_df['dollar'] = get_dollar_dict(redis_client)['price']
    except Exception as e:
        logger.error(f"get_premium_df|Exception occured! Error: {e}, traceback: {traceback.format_exc()}")
        # raise original exception
        raise e
    return premium_df