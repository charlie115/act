import time


READY_PREFIX = "WS_READY"
HEARTBEAT_PREFIX = "WS_HEARTBEAT"


def _build_ready_key(market_code, stream_type):
    return f"{READY_PREFIX}|{market_code}|{stream_type}"


def _build_heartbeat_key(market_code, stream_type, proc_name):
    return f"{HEARTBEAT_PREFIX}|{market_code}|{stream_type}|{proc_name}"


def _decode_us(raw_value):
    if raw_value is None:
        return None
    if isinstance(raw_value, bytes):
        raw_value = raw_value.decode("utf-8")
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return None


def touch_market_ready(redis_client, market_code, stream_type, timestamp_us=None, ex=180):
    if timestamp_us is None:
        timestamp_us = int(time.time() * 1_000_000)
    redis_client.set_data(
        _build_ready_key(market_code, stream_type),
        str(timestamp_us),
        ex=ex,
    )


def touch_process_heartbeat(
    redis_client,
    market_code,
    stream_type,
    proc_name,
    timestamp_us=None,
    ex=180,
):
    if timestamp_us is None:
        timestamp_us = int(time.time() * 1_000_000)
    redis_client.set_data(
        _build_heartbeat_key(market_code, stream_type, proc_name),
        str(timestamp_us),
        ex=ex,
    )


def has_recent_market_ready(
    redis_client,
    market_code,
    required_stream_types,
    max_age_secs=30,
    now_us=None,
):
    if now_us is None:
        now_us = int(time.time() * 1_000_000)
    max_age_us = int(max_age_secs * 1_000_000)
    for stream_type in required_stream_types:
        heartbeat_us = _decode_us(
            redis_client.get_data(_build_ready_key(market_code, stream_type))
        )
        if heartbeat_us is None or (now_us - heartbeat_us) > max_age_us:
            return False
    return True


def is_process_heartbeat_stale(
    redis_client,
    market_code,
    stream_type,
    proc_name,
    stale_threshold_secs=90,
    now_us=None,
):
    if now_us is None:
        now_us = int(time.time() * 1_000_000)
    heartbeat_us = _decode_us(
        redis_client.get_data(_build_heartbeat_key(market_code, stream_type, proc_name))
    )
    if heartbeat_us is None:
        return True
    return (now_us - heartbeat_us) > int(stale_threshold_secs * 1_000_000)
