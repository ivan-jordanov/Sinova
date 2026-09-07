"""TIFF dataset reader supporting single-page and multi-page stacks."""
from pathlib import Path

import numpy as np
from PIL import Image
import tifffile

from app.services.infrastructure.dataset_reader import DatasetMetadata


class TIFFReader:
    """Read each TIFF page as one projection frame."""

    def __init__(self, file_path: str):
        self.path = Path(file_path)
        if not self.path.exists():
            raise FileNotFoundError(f"TIFF file not found: {file_path}")
    
        # Memory-map the TIFF file to read dimensions without loading entire volume into RAM
        self._volume = tifffile.memmap(self.path, mode="r")
    
        # Handle 2D vs 3D TIFF stack shapes
        if self._volume.ndim == 2:
            self.projection_count = 1
            self.height, self.width = self._volume.shape
        elif self._volume.ndim == 3:
            self.projection_count, self.height, self.width = self._volume.shape
        else:
            raise ValueError(f"Unsupported TIFF dimensions: {self._volume.ndim}D")
    
        self.dtype = self._volume.dtype
        self.dtype_str = str(self.dtype)
        self.bytes_per_element = self.dtype.itemsize

    def get_metadata(self) -> DatasetMetadata:
        return DatasetMetadata(
            filename=self.path.name,
            format="TIFF",
            width=self.width,
            height=self.height,
            dtype=str(self.dtype),
            projection_count=self.projection_count,
            detector_height=self.height,
            detector_width=self.width,
        )

    def load_projection(self, frame_index: int) -> np.ndarray:
        self._validate_frame_index(frame_index)
        with Image.open(self.path) as image:
            image.seek(frame_index)
            return np.asarray(image).copy()

    def load_sinogram(self, slice_index: int) -> np.ndarray:
        self._validate_slice_index(slice_index)
        projections = [self.load_projection(index) for index in range(self.projection_count)]
        return np.stack(projections, axis=0)[:, slice_index, :]

    def _validate_frame_index(self, frame_index: int) -> None:
        if not 0 <= frame_index < self.projection_count:
            raise ValueError(
                f"Frame index {frame_index} out of bounds "
                f"(0 to {self.projection_count - 1})"
            )

    def _validate_slice_index(self, slice_index: int) -> None:
        if not 0 <= slice_index < self.height:
            raise ValueError(
                f"Slice index {slice_index} out of bounds (0 to {self.height - 1})"
            )