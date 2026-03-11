from __future__ import annotations

import os
import re
from urllib.parse import urlparse


MARKET_COMBINATION_PATTERN = re.compile(
    r"^[A-Z0-9_]+/[A-Z0-9]+:[A-Z0-9_]+/[A-Z0-9]+$"
)
BOOLEAN_TRUE_VALUES = {"1", "true", "yes", "on"}
BOOLEAN_FALSE_VALUES = {"0", "false", "no", "off"}


class ConfigValidationError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("\n".join(errors))


def parse_bool(name: str, raw_value: str | None, errors: list[str]) -> bool:
    if raw_value is None:
        errors.append(f"Missing required boolean env: {name}")
        return False

    normalized = raw_value.strip().lower()
    if normalized in BOOLEAN_TRUE_VALUES:
        return True
    if normalized in BOOLEAN_FALSE_VALUES:
        return False

    errors.append(f"Invalid boolean env {name}: {raw_value!r}")
    return False


def parse_int(
    name: str,
    raw_value: str | None,
    errors: list[str],
    *,
    minimum: int | None = None,
) -> int | None:
    if raw_value is None or raw_value == "":
        errors.append(f"Missing required integer env: {name}")
        return None

    try:
        parsed_value = int(raw_value)
    except ValueError:
        errors.append(f"Invalid integer env {name}: {raw_value!r}")
        return None

    if minimum is not None and parsed_value < minimum:
        errors.append(f"Invalid integer env {name}: {parsed_value} < {minimum}")
        return None

    return parsed_value


def require_string(name: str, raw_value: str | None, errors: list[str]) -> str:
    if raw_value is None or raw_value.strip() == "":
        errors.append(f"Missing required env: {name}")
        return ""
    return raw_value.strip()


def optional_string(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    normalized = raw_value.strip()
    return normalized or None


def parse_int_list(name: str, raw_value: str | None, errors: list[str]) -> list[int]:
    if raw_value is None or raw_value.strip() == "":
        return []

    parsed_list: list[int] = []
    for raw_item in raw_value.split(","):
        normalized_item = raw_item.strip()
        if not normalized_item:
            continue
        try:
            parsed_list.append(int(normalized_item))
        except ValueError:
            errors.append(f"Invalid integer list entry for {name}: {normalized_item!r}")
    return parsed_list


def parse_market_combination_list(
    name: str,
    raw_value: str | None,
    errors: list[str],
    *,
    required: bool = False,
) -> list[str]:
    if raw_value is None or raw_value.strip() == "":
        if required:
            errors.append(f"Missing required env: {name}")
        return []

    values: list[str] = []
    seen: set[str] = set()
    for raw_item in re.split(r"[\n,]+", raw_value):
        normalized_item = raw_item.strip()
        if not normalized_item:
            continue
        if not MARKET_COMBINATION_PATTERN.match(normalized_item):
            errors.append(
                f"Invalid market combination format in {name}: {normalized_item!r}"
            )
            continue
        if normalized_item in seen:
            errors.append(f"Duplicate market combination in {name}: {normalized_item}")
            continue
        seen.add(normalized_item)
        values.append(normalized_item)

    if required and not values:
        errors.append(f"{name} must contain at least one market combination")
    return values


def validate_url(name: str, raw_value: str | None, errors: list[str]) -> str:
    normalized_value = require_string(name, raw_value, errors)
    if not normalized_value:
        return ""

    parsed_url = urlparse(normalized_value)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        errors.append(f"Invalid URL env {name}: {normalized_value!r}")
    return normalized_value


def validate_config_path(config_path: str, errors: list[str]) -> str:
    if not config_path:
        errors.append("Config path is empty")
        return config_path

    if not os.path.exists(config_path):
        errors.append(f"Config file does not exist: {config_path}")
    return config_path


def ensure_valid(errors: list[str]):
    if errors:
        raise ConfigValidationError(errors)
