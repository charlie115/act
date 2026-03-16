"""Backward-compatible re-export from acw_common."""

from _acw_common import ensure_acw_common_on_path

ensure_acw_common_on_path()

from acw_common.db.mongodb_client import InitDBClient  # noqa: F401, E402
