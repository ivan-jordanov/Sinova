"""Configuration and settings for SINOVA backend."""
from pathlib import Path
import os

# Operation dependencies: if key op is enabled, all values must be enabled first
OPERATION_DEPENDENCIES: dict[str, list[str]] = {
    "normalize": [],
    "negative_log": ["normalize"],
    "clip_attenuation": [],
    "fov_mask": [],
    "crop_pad_beam": [],
    "denoise": [],
    "cor_shift": [],
    "ring_filter_fw": [],
    "ring_filter_vo": [],
    "neural": [],
}

# Operation scope: Specifies valid preview context applicability ("projection", "sinogram", or "both")
OPERATION_SCOPES: dict[str, str] = {
    "normalize": "both",
    "negative_log": "both",
    "clip_attenuation": "both",
    "fov_mask": "projection",
    "crop_pad_beam": "projection",
    "denoise": "both",
    "cor_shift": "sinogram",
    "ring_filter_fw": "sinogram",
    "ring_filter_vo": "sinogram",
    "neural": "sinogram",
}

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