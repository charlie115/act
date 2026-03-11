import datetime


_DOLLAR_REDIS_KEY = "INFO_CORE|dollar"
_DOLLAR_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
_DEFAULT_MAX_AGE_SECONDS = 180


def _is_stale(dollar_dict, max_age_seconds):
    if not dollar_dict:
        return True

    last_updated_time = dollar_dict.get("last_updated_time")
    if not last_updated_time:
        return True

    try:
        last_updated_dt = datetime.datetime.strptime(
            last_updated_time,
            _DOLLAR_TIMESTAMP_FORMAT,
        )
    except (TypeError, ValueError):
        return True

    age_seconds = (datetime.datetime.utcnow() - last_updated_dt).total_seconds()
    return age_seconds > max_age_seconds


def get_dollar_dict(
    redis_client,
    fallback_redis_client=None,
    max_age_seconds=_DEFAULT_MAX_AGE_SECONDS,
):
    fallback_redis_client = fallback_redis_client or getattr(
        redis_client,
        "fallback_redis_client",
        None,
    )
    dollar_dict = redis_client.get_dict(_DOLLAR_REDIS_KEY)

    if not _is_stale(dollar_dict, max_age_seconds):
        return dollar_dict

    if fallback_redis_client is None:
        return dollar_dict

    fallback_dollar_dict = fallback_redis_client.get_dict(_DOLLAR_REDIS_KEY)
    if fallback_dollar_dict is None:
        return dollar_dict

    if dollar_dict is None or not _is_stale(fallback_dollar_dict, max_age_seconds):
        redis_client.set_dict(_DOLLAR_REDIS_KEY, fallback_dollar_dict)
        return fallback_dollar_dict

    return dollar_dict or fallback_dollar_dict
