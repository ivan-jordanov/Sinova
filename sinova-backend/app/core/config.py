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

# Operation scope: how much data an operation needs to actually run.
#   "slice"   -> only the single projection/sinogram row currently selected
#   "stack"   -> the full projection or sinogram stack for the active context
#   "dataset" -> data spanning both contexts / the whole dataset
#
# This does NOT change how an operation is applied once it has concrete
# parameters -- apply_single_operation still just runs on whatever array
# it's given. Scope only matters for operations whose *parameters* can't
# be known from a single slice (currently just COR estimation). See
# resolve_broad_scope_operation() in operation_executor.py.
OPERATION_SCOPES: dict[str, str] = {
    "normalize": "slice",
    "negative_log": "slice",
    "denoise": "slice",
    # Real stripe removal (preprocessing_ops.ring_filter) works better across
    # a full sinogram stack than a single row. Left as "slice" for now since
    # the executor still runs it per-row -- revisit if/when ring_filter is
    # wired up to operate on the full stack.
    "ring_filter": "slice",
    "edge_enhance": "slice",  # STILL INCOMPLETE -- see operation_executor.apply_single_operation
    "fov_mask": "slice",
    # Applying a *known* COR offset is slice-level. ESTIMATING that offset
    # needs the broader sinogram stack -- see resolve_broad_scope_operation().
    "cor": "slice",
    "clip_attenuation": "slice",
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