"""Configuration and settings for SINOVA backend."""
import os
from pathlib import Path

from app.core.constants import (
    BROAD_SCOPE_OPERATIONS,
    GPU_BOUND_OPERATIONS,
    OPERATION_DEPENDENCIES,
    OPERATION_SCOPES,
)
from app.schemas.preprocessing import OperationInfo

AVAILABLE_OPERATIONS = [
    OperationInfo(
        id="normalization",
        name="Normalization",
        short_name="normalize",
        category="intensity",
        description="Normalize intensity values using flat/dark references",
        requires=[],
        scope=OPERATION_SCOPES["normalize"],
    ),
    # ... rest of AVAILABLE_OPERATIONS ...
]


class Settings:
    """Application settings."""

    DATA_ROOT = Path(os.getenv("SINOVA_DATA_ROOT", "./data"))
    CACHE_DIR = DATA_ROOT / "cache"
    OUTPUT_DIR = DATA_ROOT / "outputs"

    ALLOWED_PATHS = [
        Path("/data/scans"),
        Path.home() / "Documents" / "scans",
    ]

    MAX_FILE_SIZE = 500 * 1024 * 1024 * 1024
    TEMP_BUFFER_SIZE = 1024 * 1024 * 10


settings = Settings()