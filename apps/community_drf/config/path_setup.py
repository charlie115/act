from pathlib import Path
import sys


def append_local_apps_path(base_dir: Path):
    apps_path = str(base_dir / "apps")
    if apps_path not in sys.path:
        sys.path.append(apps_path)
