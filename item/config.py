import json
import os
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "item"
CONFIG_FILE = CONFIG_DIR / "config.json"


def get_list_id() -> str | None:
    """Return the active task list ID from the config file."""
    if CONFIG_FILE.exists():
        data = json.loads(CONFIG_FILE.read_text())
        return data.get("list_id") or None
    return None


def set_default_list(list_id: str) -> None:
    """Persist list_id as the default in the config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data: dict = {}
    if CONFIG_FILE.exists():
        data = json.loads(CONFIG_FILE.read_text())
    data["list_id"] = list_id
    CONFIG_FILE.write_text(json.dumps(data, indent=2) + "\n")
