"""Read optional metadata sidecars for headerless raw datasets."""
import json
from pathlib import Path


def read_raw_metadata(path: Path) -> dict[str, object]:
    """Read ``<dataset>.json`` when present, otherwise return empty metadata."""
    sidecar = path.with_suffix(".json")
    if not sidecar.exists():
        return {}

    try:
        value = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid raw dataset metadata sidecar: {sidecar}") from error

    if not isinstance(value, dict):
        raise ValueError(f"Raw dataset metadata sidecar must contain an object: {sidecar}")
    return value