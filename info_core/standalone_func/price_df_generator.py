import pandas as pd
from etc.redis_connector.redis_helper import RedisHelper
import numpy as np
import traceback
import _pickle as pickle

def get_binance_price_df(redis_client, market_type):
    binance_ticker_df = pd.DataFrame(redis_client.get_all_exchange_stream_data("ticker", f"BINANCE_{market_type}")).T.reset_index(drop=True)[['s','P','c','v','q']]
    binance_ticker_df.rename(columns={"q": "atp24h", 'P': 'scr', 'c': 'tp'}, inplace=True)
    binance_bookticker_df = pd.DataFrame(redis_client.get_all_exchange_stream_data("orderbook", f"BINANCE_{market_type}")).T.reset_index(drop=True)[['s','b','a']]
    binance_bookticker_df.rename(columns={"b": "bp", "a": "ap"}, inplace=True)
    binance_merged_df = pd.merge(binance_ticker_df, binance_bookticker_df, on='s', how='inner')
    binance_merged_df[['scr','tp','atp24h','ap','bp']] = binance_merged_df[['scr','tp','atp24h','ap','bp']].astype(float)
    binance_info_df = pickle.loads(redis_client.get_data(f'binance_{market_type.lower()}_info_df'))[['symbol','base_asset','quote_asset']]
    binance_merged_df = binance_merged_df.merge(binance_info_df, left_on='s', right_on='symbol', how='inner')
    binance_merged_df.drop(['symbol', 's'], axis=1, inplace=True)
    return binance_merged_df

def get_bithumb_price_df(redis_client):
    orderbook_df = pd.DataFrame(redis_client.get_all_exchange_stream_data("orderbook", "BITHUMB_SPOT")).T.reset_index()
    ticker_df = pd.DataFrame(redis_client.get_all_exchange_stream_data("ticker", "BITHUMB_SPOT")).T.reset_index()

    # Drop records where bids data is an empty list
    orderbook_df = orderbook_df[orderbook_df['bids'].apply(lambda x: len(x) > 0)]
    
    # Extract the first price from asks and bids
    orderbook_df['best_ask'] = orderbook_df['asks'].apply(lambda x: x[0][0])
    orderbook_df['best_bid'] = orderbook_df['bids'].apply(lambda x: x[0][0])

    # Continue only if the DataFrame is not empty after dropping rows
    if orderbook_df.empty:
        print("WARN: Bithumb orderbook DataFrame became empty after removing rows with invalid asks/bids.")
        # Return an empty DataFrame with expected columns to avoid downstream errors
        return pd.DataFrame(columns=['symbol', 'best_ask', 'best_bid', 'tp', 'scr', 'atp24h', 'base_asset', 'quote_asset', 'ap', 'bp'])

    merged_df = orderbook_df.merge(ticker_df[['symbol','closePrice','chgRate','value']], on='symbol', how='inner')
    merged_df[['base_asset', 'quote_asset']] = merged_df['symbol'].str.split('_', expand=True)
    merged_df = merged_df.rename(columns={'value':'atp24h', 'chgRate':'scr', 'closePrice': 'tp', 'best_ask':'ap', 'best_bid':'bp'})

    # Convert to float
    merged_df[['scr','atp24h','tp','ap','bp']] = merged_df[['scr','atp24h','tp','ap','bp']].astype(float)

    # merged_df['tp'] = (merged_df['ap'] + merged_df['bp']) / 2 # This line can now potentially operate on NaN if ap/bp were NaN
    # Consider how to handle NaN values if using this calculation, e.g., dropna beforehand or use pandas functions that handle NaN.

    return merged_df

def get_bybit_price_df(redis_client, market_type):
    ticker_df = pd.DataFrame(redis_client.get_all_exchange_stream_data("ticker", f"BYBIT_{market_type}")).T.reset_index()
    orderbook_df = pd.DataFrame(redis_client.get_all_exchange_stream_data("orderbook", f"BYBIT_{market_type}")).T.reset_index()
    merged_df = ticker_df.merge(orderbook_df, left_on='symbol', right_on='s', how='inner')
    bybit_info_df = pickle.loads(redis_client.get_data(f'bybit_{market_type.lower()}_info_df'))[['symbol','base_asset','quote_asset']]
    merged_df = merged_df.merge(bybit_info_df, on='symbol', how='inner')
    merged_df['b'] = merged_df['b'].apply(lambda x: x[0][0])
    merged_df['a'] = merged_df['a'].apply(lambda x: x[0][0])
    merged_df['price24hPcnt'] = merged_df['price24hPcnt'].astype(float) * 100
    if market_type == "COIN_M":
        merged_df = merged_df.rename(columns={"lastPrice":'tp', 'a':'ap', 'b':'bp', 'price24hPcnt':'scr', 'volume24h':'atp24h'})
    else:
        merged_df = merged_df.rename(columns={"lastPrice":'tp', 'a':'ap', 'b':'bp', 'price24hPcnt':'scr', 'turnover24h':'atp24h'})
    merged_df[['tp','ap','bp','scr','atp24h']] = merged_df[['tp','ap','bp','scr','atp24h']].astype(float)
    merged_df = merged_df[['symbol','base_asset','quote_asset','tp','bp','ap','scr','atp24h']]
    return merged_df

def get_okx_price_df(redis_client, market_type):
    try:
        ticker_df = pd.DataFrame(redis_client.get_all_exchange_stream_data("ticker", f"OKX_{market_type}")).T
        ticker_df['base_asset'] = ticker_df['instId'].apply(lambda x: x.split('-')[0])
        ticker_df['quote_asset'] = ticker_df['instId'].apply(lambda x: x.split('-')[1])
        ticker_df = ticker_df.rename(columns={"last": "tp", "askPx": "ap", "bidPx":"bp", "volCcy24h":"atp24h"})
        ticker_df[['tp', 'ap', 'bp', 'open24h', 'atp24h']] = ticker_df[['tp', 'ap', 'bp', 'open24h', 'atp24h']].astype(float)
        ticker_df['atp24h'] = ticker_df.apply(lambda x: x['tp']*x['atp24h'] if x['instType'] != "SPOT" else x['atp24h'], axis=1)
        ticker_df['scr'] = (ticker_df['tp'] - ticker_df['open24h']) / ticker_df['open24h'] * 100
        ticker_df = ticker_df[['instId', 'base_asset', 'quote_asset', 'tp', 'ap', 'bp', 'scr', 'atp24h']]
        return ticker_df
    except Exception as e:
        content = f"get_price_df|{traceback.format_exc()}"
        # Handle logging or error handling here
        raise e

def get_upbit_price_df(redis_client):
    upbit_ticker_df = pd.DataFrame(redis_client.get_all_exchange_stream_data("ticker", "UPBIT_SPOT")).T.reset_index()[['index','tp','scr','atp24h','h52wp','l52wp','ms','mw','tms']]
    upbit_orderbook_df = pd.DataFrame(redis_client.get_all_exchange_stream_data("orderbook", "UPBIT_SPOT")).T.reset_index(drop=True)[['cd','tms','obu']]
    upbit_orderbook_df['ap'] = upbit_orderbook_df['obu'].apply(lambda x: x[0]['ap'])
    upbit_orderbook_df['bp'] = upbit_orderbook_df['obu'].apply(lambda x: x[0]['bp'])
    upbit_orderbook_df.drop('obu', axis=1, inplace=True)
    upbit_merged_df = pd.merge(upbit_ticker_df, upbit_orderbook_df, left_on='index', right_on='cd', how='inner')
    upbit_merged_df = upbit_merged_df.dropna(subset=['tp', 'ap', 'bp'])
    upbit_merged_df['base_asset'] = upbit_merged_df['index'].apply(lambda x: x.split('-')[1])
    upbit_merged_df['quote_asset'] = upbit_merged_df['index'].apply(lambda x: x.split('-')[0])
    upbit_merged_df.drop('index', axis=1, inplace=True)
    upbit_merged_df[['scr','atp24h','h52wp','l52wp','ap','bp']] = upbit_merged_df[['scr','atp24h','h52wp','l52wp','ap','bp']].astype(float)
    upbit_merged_df['scr'] = upbit_merged_df['scr'] * 100
    return upbit_merged_df

def get_gate_price_df(redis_client, market_type):
    """
    Get price DataFrame for Gate.io futures.

    Gate.io ticker data format (from websocket):
    - s: symbol (e.g., BTC_USDT)
    - c: last price
    - P: price change percentage
    - q: 24h quote volume (USDT)

    Gate.io orderbook data format:
    - s: symbol
    - b: best bid price
    - a: best ask price
    """
    ticker_data = redis_client.get_all_exchange_stream_data("ticker", f"GATE_{market_type}")
    orderbook_data = redis_client.get_all_exchange_stream_data("orderbook", f"GATE_{market_type}")

    if not ticker_data or not orderbook_data:
        return pd.DataFrame(columns=['symbol', 'base_asset', 'quote_asset', 'tp', 'bp', 'ap', 'scr', 'atp24h'])

    ticker_df = pd.DataFrame(ticker_data).T.reset_index(drop=True)
    orderbook_df = pd.DataFrame(orderbook_data).T.reset_index(drop=True)

    # Select relevant columns from ticker (s=symbol, c=close/last, P=change%, q=quote volume)
    ticker_df = ticker_df[['s', 'c', 'P', 'q']].copy()
    ticker_df = ticker_df.rename(columns={'c': 'tp', 'P': 'scr', 'q': 'atp24h'})

    # Select relevant columns from orderbook (s=symbol, b=bid, a=ask)
    orderbook_df = orderbook_df[['s', 'b', 'a']].copy()
    orderbook_df = orderbook_df.rename(columns={'b': 'bp', 'a': 'ap'})

    # Merge ticker and orderbook
    merged_df = ticker_df.merge(orderbook_df, on='s', how='inner')

    # Convert to float
    merged_df[['tp', 'scr', 'atp24h', 'bp', 'ap']] = merged_df[['tp', 'scr', 'atp24h', 'bp', 'ap']].astype(float)

    # Get info for base_asset and quote_asset
    gate_info_df = pickle.loads(redis_client.get_data(f'gate_{market_type.lower()}_info_df'))[['symbol', 'base_asset', 'quote_asset']]
    merged_df = merged_df.merge(gate_info_df, left_on='s', right_on='symbol', how='inner')
    merged_df.drop(['symbol', 's'], axis=1, inplace=True)

    return merged_df


EXCHANGE_HANDLERS = {
    "BINANCE": get_binance_price_df,
    "BITHUMB": get_bithumb_price_df,
    "BYBIT": get_bybit_price_df,
    "OKX": get_okx_price_df,
    "UPBIT": get_upbit_price_df,
    "GATE": get_gate_price_df
}

def get_price_df(redis_client, market_code):
    exchange = market_code.split('_')[0]
    # all the part excluding exchange
    market_type = '_'.join(market_code.split('_')[1:])
    exchange = exchange.upper()
    market_type = market_type.upper()

    handler = EXCHANGE_HANDLERS.get(exchange)
    if handler:
        if exchange in ["BINANCE", "BYBIT", "OKX", "GATE"]:
            return handler(redis_client, market_type)
        else:
            return handler(redis_client)
    else:
        raise ValueError(f"get_price_df|exchange: {exchange} is not supported!")