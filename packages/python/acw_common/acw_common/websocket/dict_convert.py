import pandas as pd

def get_ticker_ratio(price_krw):
    if price_krw == 0:
        return 0
    if price_krw < 0.1:
        ticker_size = 0.0001
    elif price_krw < 1:
        ticker_size = 0.001
    elif price_krw < 10:
        ticker_size = 0.01
    elif price_krw < 100:
        ticker_size = 0.1
    elif price_krw < 1000:
        ticker_size = 1
    elif price_krw < 10000:
        ticker_size = 5
    elif price_krw < 100000:
        ticker_size = 10
    elif price_krw < 500000:
        ticker_size = 50
    elif price_krw < 1000000:
        ticker_size = 100
    elif price_krw < 2000000:
        ticker_size = 500
    elif price_krw >= 2000000:
        ticker_size = 1000
    ticker_ratio = ticker_size / price_krw
    return ticker_ratio

def okx_ticker_convert(OKX_TICKER_DICT):
    OKX_TICKER_DICT_copy = dict(OKX_TICKER_DICT.copy())
    converted_df = pd.DataFrame(OKX_TICKER_DICT_copy).transpose().reset_index(drop=True)
    return converted_df

def upbit_ticker_convert(UPBIT_TICKER_DICT):
    UPBIT_TICKER_DICT_copy = dict(UPBIT_TICKER_DICT.copy())
    converted_df = pd.DataFrame(UPBIT_TICKER_DICT_copy).transpose().reset_index(drop=True)
    return converted_df

def upbit_orderbook_convert(UPBIT_ORDERBOOK_DICT):
    UPBIT_ORDERBOOK_DICT_copy = dict(UPBIT_ORDERBOOK_DICT.copy())
    converted_df = pd.DataFrame(UPBIT_ORDERBOOK_DICT_copy).transpose().reset_index(drop=True)
    return converted_df

def get_kimp_df(OKX_TICKER_DICT, UPBIT_TICKER_DICT, UPBIT_ORDERBOOK_DICT, current_dollar):
    upbit_allticker_df = upbit_ticker_convert(UPBIT_TICKER_DICT)
    okx_ticker_df = okx_ticker_convert(OKX_TICKER_DICT)
    upbit_orderbook_df = upbit_orderbook_convert(UPBIT_ORDERBOOK_DICT)
    upbit_allticker_df = upbit_allticker_df.merge(upbit_orderbook_df, on='cd')
    upbit_allticker_df.loc[:, 'cd'] = upbit_allticker_df['cd'].apply(lambda x: x.replace('KRW-', ''))
    okx_ticker_df.loc[:, 's'] = okx_ticker_df['instId'].str.replace('-USDT-SWAP', '')
    merged_allticker_df = upbit_allticker_df.merge(okx_ticker_df, left_on='cd', right_on='s')
    merged_allticker_df.loc[:, ['last', 'askPx', 'bidPx']] = merged_allticker_df.loc[:, ['last', 'askPx', 'bidPx']].astype(float)
    merged_allticker_df['okx_bid_price_krw'] = merged_allticker_df['bidPx'] * current_dollar
    merged_allticker_df['okx_ask_price_krw'] = merged_allticker_df['askPx'] * current_dollar
    merged_allticker_df['okx_last_price_krw'] = merged_allticker_df['last'] * current_dollar
    merged_allticker_df = merged_allticker_df[
        merged_allticker_df['obu'].apply(lambda x: len(x) > 0)
    ]
    merged_allticker_df['upbit_ask_price'] = merged_allticker_df['obu'].apply(lambda x: x[0]['ap'])
    merged_allticker_df['upbit_bid_price'] = merged_allticker_df['obu'].apply(lambda x: x[0]['bp'])

    merged_allticker_df['enter_kimp'] = (merged_allticker_df['upbit_ask_price'] - merged_allticker_df['okx_bid_price_krw']) / merged_allticker_df['okx_bid_price_krw']
    merged_allticker_df['exit_kimp'] = (merged_allticker_df['upbit_bid_price'] - merged_allticker_df['okx_ask_price_krw']) / merged_allticker_df['okx_ask_price_krw']
    merged_allticker_df['tp_kimp'] = (merged_allticker_df['tp'] - merged_allticker_df['okx_last_price_krw']) / merged_allticker_df['okx_last_price_krw']
    merged_allticker_df['enter_usdt'] = (merged_allticker_df['enter_kimp'] + 1) * current_dollar
    merged_allticker_df['exit_usdt'] = (merged_allticker_df['exit_kimp'] + 1) * current_dollar
    merged_allticker_df['tp_usdt'] = (merged_allticker_df['tp_kimp'] + 1) * current_dollar
    merged_allticker_df = merged_allticker_df.rename(columns={
        's': 'symbol',
        'atp24h': 'acc_trade_price_24h',
        'tp': 'trade_price',
        'bidPx': 'okx_bid_price',
        'askPx': 'okx_ask_price',
        'scr': 'signed_change_rate',
        'ms': 'upbit_market_state',
        'dd': 'upbit_delisting_date',
        'its': 'upbit_is_trading_suspended',
        'tms_x': 'upbit_timestamp',
        'ts': 'okx_timestamp',
        'last': 'okx_last_price'
    })
    kimp_df = (merged_allticker_df[['symbol', 'acc_trade_price_24h', 'trade_price', 'okx_bid_price', 'okx_ask_price', 'okx_last_price', 'signed_change_rate',
                                    'upbit_market_state', 'upbit_delisting_date', 'upbit_is_trading_suspended',
                                    'upbit_timestamp', 'okx_timestamp', 'enter_kimp', 'exit_kimp', 'tp_kimp', 'enter_usdt', 'exit_usdt', 'tp_usdt']])
    return kimp_df
