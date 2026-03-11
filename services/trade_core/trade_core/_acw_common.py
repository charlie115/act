from pathlib import Path
import sys


def ensure_acw_common_on_path():
    candidates = [
        Path(__file__).resolve().parents[3] / "packages" / "python" / "acw_common",
        Path("/opt/acw_common"),
    ]

    for candidate in candidates:
        candidate_str = str(candidate)
        if candidate.exists() and candidate_str not in sys.path:
            sys.path.insert(0, candidate_str)

