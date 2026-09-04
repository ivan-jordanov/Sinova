"""Configuration and settings for SINOVA backend."""
from pathlib import Path
import os

# Operation dependencies: if key op is enabled, all values must be enabled first
OPERATION_DEPENDENCIES = {
    "normalize": [],
    "negative_log": ["normalize"],
    "denoise": [],
    "ring_filter": [],
    "edge_enhance": ["denoise"],
}


class Settings:
    """Application settings."""

    # Data directories
    DATA_ROOT = Path(os.getenv("SINOVA_DATA_ROOT", "./data"))
    CACHE_DIR = DATA_ROOT / "cache"
    OUTPUT_DIR = DATA_ROOT / "outputs"

    # Security: paths where we allow reading files
    ALLOWED_PATHS = [
        Path("/data/scans"),
        Path.home() / "Documents" / "scans",
    ]

    # File size limits (500 GB)
    MAX_FILE_SIZE = 500 * 1024 * 1024 * 1024

    # Temporary buffer size for chunked reads (10 MB)
    TEMP_BUFFER_SIZE = 1024 * 1024 * 10


settings = Settings()
