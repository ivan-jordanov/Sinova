"""Shared path validation for supported dataset readers."""
from pathlib import Path

from app.core.config import settings


def validate_path(user_path: str) -> Path:
    try:
        path = Path(user_path).resolve()
    except Exception as e:
        raise ValueError(f"Invalid path syntax: {user_path}") from e

    # Check existence
    if not path.exists():
        raise ValueError(f"File not found: {path}")

    # Security: whitelist allowed directories
    # Safely convert allowed entries to resolved Path objects
    allowed_paths = [Path(p).resolve() for p in settings.ALLOWED_PATHS if Path(p).exists()]
    
    if allowed_paths:
        is_allowed = any(path.is_relative_to(allowed) for allowed in allowed_paths)
        if not is_allowed:
            allowed_str = ", ".join(str(p) for p in allowed_paths)
            raise ValueError(f"Path not whitelisted. Allowed: {allowed_str}")

    # Check file size
    size = path.stat().st_size
    if size > settings.MAX_FILE_SIZE:
        raise ValueError(
            f"File too large: {size / 1e9:.1f} GB (max: {settings.MAX_FILE_SIZE / 1e9:.1f} GB)"
        )

    return path