import json
from pathlib import Path
from typing import Any

import yaml


def load_profile(path: str | Path) -> dict:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        return yaml.safe_load(text)
    if path.suffix == ".json":
        return json.loads(text)
    raise ValueError(f"Unsupported profile format: {path.suffix!r} (use .yaml, .yml, or .json)")


def load_aliases(path: str | Path) -> tuple[dict[str, list[str]], set[str], set[str]]:
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    exclude = set(data.pop("_exclude", []))
    overwrite = set(data.pop("_overwrite", []))
    aliases = {k: [str(v) for v in vs] for k, vs in data.items()}
    return aliases, exclude, overwrite


def flatten_profile(profile: dict) -> dict[str, Any]:
    """Flatten nested profile dict into dotted-path keys, preserving lists at each level."""
    result: dict[str, Any] = {}
    _flatten(profile, "", result)
    return result


def _flatten(obj: Any, prefix: str, result: dict) -> None:
    if isinstance(obj, dict):
        if prefix:  # Store the dict itself (e.g. period: {start, end}) but skip root
            result[prefix] = obj
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            _flatten(v, key, result)
    elif isinstance(obj, list):
        result[prefix] = obj
        for i, item in enumerate(obj):
            _flatten(item, f"{prefix}.{i}", result)
    else:
        result[prefix] = obj
