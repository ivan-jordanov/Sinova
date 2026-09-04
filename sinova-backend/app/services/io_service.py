"""Dataset I/O boundary reserved for MRAW, TIFF, and HDF5 readers."""
from pathlib import Path

from app.core.config import settings


def validate_path(user_path: str) -> Path:
    """
    Validate and resolve a user-provided file path.

    Args:
        user_path: Path string from user (e.g., "/data/scans/spider.mraw")

    Returns:
        Resolved Path object

    Raises:
        ValueError: If path is invalid, not found, not whitelisted, or too large
    """
    try:
        path = Path(user_path).resolve()
    except Exception as e:
        raise ValueError(f"Invalid path syntax: {user_path}") from e

    # Check if path exists
    if not path.exists():
        raise ValueError(f"File not found: {path}")

    # Security: whitelist allowed directories
    is_allowed = any(
        path.is_relative_to(allowed)
        for allowed in settings.ALLOWED_PATHS
        if allowed.exists()
    )
    if not is_allowed:
        allowed_str = ", ".join(str(p) for p in settings.ALLOWED_PATHS)
        raise ValueError(
            f"Path not whitelisted. Allowed: {allowed_str}"
        )

    # Check file size
    size = path.stat().st_size
    if size > settings.MAX_FILE_SIZE:
        raise ValueError(
            f"File too large: {size / 1e9:.1f} GB (max: {settings.MAX_FILE_SIZE / 1e9:.1f} GB)"
        )

    return path