from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured


def _is_blank(value):
    return value is None or str(value).strip() == ""


def _validate_url(name, value, allowed_schemes, errors):
    if _is_blank(value):
        errors.append(f"Missing required env: {name}")
        return
    parsed = urlparse(value)
    if parsed.scheme not in allowed_schemes or _is_blank(parsed.netloc):
        errors.append(f"Invalid {name}: {value!r}")


def validate_runtime_env(env):
    errors = []

    django_secret_key = env("DJANGO_SECRET_KEY", default="")
    if _is_blank(django_secret_key):
        errors.append("Missing required env: DJANGO_SECRET_KEY")

    _validate_url(
        "COMMUNITY_DB_URL",
        env("COMMUNITY_DB_URL", default=""),
        {"postgres", "postgresql", "postgresql+psycopg2"},
        errors,
    )
    _validate_url(
        "NEWSCORE_DB_URL",
        env("NEWSCORE_DB_URL", default=""),
        {"postgres", "postgresql", "postgresql+psycopg2"},
        errors,
    )
    _validate_url(
        "MESSAGECORE_DB_URL",
        env("MESSAGECORE_DB_URL", default=""),
        {"postgres", "postgresql", "postgresql+psycopg2"},
        errors,
    )
    _validate_url(
        "REDIS_DB_URL",
        env("REDIS_DB_URL", default=""),
        {"redis", "rediss"},
        errors,
    )

    mongodb_host = env("MONGODB_HOST", default="")
    if _is_blank(mongodb_host):
        errors.append("Missing required env: MONGODB_HOST")

    mongodb_port = env.int("MONGODB_PORT", default=27017)
    if mongodb_port <= 0:
        errors.append(f"Invalid MONGODB_PORT: {mongodb_port}")

    wallet_api_key_file = env("WALLET_API_KEY_FILE", default="")
    if wallet_api_key_file and not __import__("os").path.exists(wallet_api_key_file):
        errors.append(f"WALLET_API_KEY_FILE does not exist: {wallet_api_key_file}")

    if errors:
        raise ImproperlyConfigured("\n".join(errors))


def validate_prod_hosts(env, allowed_hosts):
    if not allowed_hosts:
        raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must not be empty in production")

    csrf_origins = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])
    if not csrf_origins:
        raise ImproperlyConfigured("DJANGO_CSRF_TRUSTED_ORIGINS must not be empty in production")
