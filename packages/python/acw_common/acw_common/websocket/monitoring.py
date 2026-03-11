import time

from .freshness import get_stale_symbol_summary
from .heartbeat import has_recent_market_ready, is_process_heartbeat_stale


def wait_for_market_ready(
    redis_client,
    market_code,
    required_stream_types,
    logger,
    wait_message,
    *,
    loop_sleep_secs=2,
    timeout_secs=None,
):
    start_time = time.time()
    while True:
        if has_recent_market_ready(redis_client, market_code, required_stream_types):
            return True
        logger.info(wait_message)
        if timeout_secs is not None and (time.time() - start_time) > timeout_secs:
            return False
        time.sleep(loop_sleep_secs)


def evaluate_process_staleness(
    redis_client,
    market_code,
    stream_type,
    proc_name,
    symbol_list,
    partial_stale_strikes,
    *,
    stale_threshold_secs=90,
    now_us=None,
    required_strikes=2,
    min_stale_symbols=2,
    min_stale_ratio=0.25,
):
    now_us = now_us or int(time.time() * 1_000_000)

    if not symbol_list:
        partial_stale_strikes.pop(proc_name, None)
        return {"action": "skip", "reason": "no_symbols"}

    if is_process_heartbeat_stale(
        redis_client,
        market_code,
        stream_type,
        proc_name,
        stale_threshold_secs=stale_threshold_secs,
        now_us=now_us,
    ):
        partial_stale_strikes.pop(proc_name, None)
        return {"action": "restart", "reason": "heartbeat"}

    summary = get_stale_symbol_summary(
        redis_client,
        market_code,
        stream_type,
        symbol_list,
        stale_threshold_secs=stale_threshold_secs,
        now_us=now_us,
    )
    stale_count = summary["stale_count"]
    total_symbols = summary["total_symbols"]
    stale_ratio = summary["stale_ratio"]
    stale_symbols_preview = summary["stale_symbols"][:5]

    if stale_count == 0:
        partial_stale_strikes.pop(proc_name, None)
        return {"action": "healthy", "reason": "fresh"}

    strike_count = partial_stale_strikes.get(proc_name, 0) + 1
    partial_stale_strikes[proc_name] = strike_count

    if stale_count == total_symbols:
        partial_stale_strikes.pop(proc_name, None)
        return {
            "action": "restart",
            "reason": "all_symbols",
            "stale_count": stale_count,
            "total_symbols": total_symbols,
            "strike_count": strike_count,
            "stale_ratio": stale_ratio,
            "stale_symbols_preview": stale_symbols_preview,
        }

    if strike_count >= required_strikes and (
        stale_count >= min(min_stale_symbols, total_symbols) or stale_ratio >= min_stale_ratio
    ):
        partial_stale_strikes.pop(proc_name, None)
        return {
            "action": "restart",
            "reason": "partial_persisted",
            "stale_count": stale_count,
            "total_symbols": total_symbols,
            "strike_count": strike_count,
            "stale_ratio": stale_ratio,
            "stale_symbols_preview": stale_symbols_preview,
        }

    return {
        "action": "warn",
        "reason": "partial_once",
        "stale_count": stale_count,
        "total_symbols": total_symbols,
        "strike_count": strike_count,
        "stale_ratio": stale_ratio,
        "stale_symbols_preview": stale_symbols_preview,
    }
