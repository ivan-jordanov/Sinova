"""Shared contracts for dataset format readers."""
from typing import Protocol, TypedDict

import numpy as np


class DatasetMetadata(TypedDict):
    """Metadata returned by every supported dataset reader."""

    filename: str
    format: str
    width: int
    height: int
    dtype: str
    projection_count: int
    detector_height: int
    detector_width: int


class DatasetReader(Protocol):
    """Interface used by the business dataset service."""

    def get_metadata(self) -> DatasetMetadata: ...

    def load_projection(self, frame_index: int) -> np.ndarray: ...

    def load_sinogram(self, slice_index: int) -> np.ndarray: ...