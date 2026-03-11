import time


def get_stale_symbol_summary(
    redis_client,
    market_code,
    stream_type,
    symbol_list,
    *,
    stale_threshold_secs=90,
    now_us=None,
):
    now_us = now_us or int(time.time() * 1_000_000)
    stale_threshold_us = int(stale_threshold_secs * 1_000_000)
    stale_symbols = []

    for symbol in symbol_list:
        symbol_data = redis_client.get_exchange_stream_data(stream_type, market_code, symbol) or {}
        last_update_us = symbol_data.get("last_update_timestamp")
        if last_update_us is None:
            stale_symbols.append(symbol)
            continue
        try:
            if now_us - int(last_update_us) > stale_threshold_us:
                stale_symbols.append(symbol)
        except (TypeError, ValueError):
            stale_symbols.append(symbol)

    total_symbols = len(symbol_list)
    stale_count = len(stale_symbols)
    stale_ratio = (stale_count / total_symbols) if total_symbols else 0.0
    return {
        "total_symbols": total_symbols,
        "stale_count": stale_count,
        "stale_ratio": stale_ratio,
        "stale_symbols": stale_symbols,
    }
