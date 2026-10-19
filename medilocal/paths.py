"""Per-user paths; importing this module never creates files."""
import json
import os
import sys
import tempfile
from pathlib import Path


def data_dir():
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "MediLocal"
    base = Path(os.environ.get("XDG_DATA_HOME", ""))
    if not base.is_absolute():
        base = Path.home() / ".local/share"
    return base / "medilocal"


def private_dir(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name != "nt":
        path.chmod(0o700)
    return path


def private_file(path):
    if os.name != "nt":
        Path(path).chmod(0o600)


def load_settings(directory=None):
    defaults = {"language": "es", "theme": "dark", "font_size": 12}
    try:
        raw = json.loads(((directory or data_dir()) / "settings.json").read_text(encoding="utf-8"))
        if raw.get("language") in ("es", "en"):
            defaults["language"] = raw["language"]
        if raw.get("theme") in ("light", "dark"):
            defaults["theme"] = raw["theme"]
        if type(raw.get("font_size")) is int and 10 <= raw["font_size"] <= 20:
            defaults["font_size"] = raw["font_size"]
    except (OSError, ValueError, AttributeError):
        pass
    return defaults


def save_settings(settings, directory=None):
    directory = private_dir(directory or data_dir())
    fd, name = tempfile.mkstemp(prefix="settings-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(settings, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, directory / "settings.json")
    finally:
        Path(name).unlink(missing_ok=True)


def legacy_candidates():
    root = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
    return [root / "data/medilocal.db"]
