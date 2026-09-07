"""Raw .dat dataset reader with optional JSON sidecar metadata."""
from pathlib import Path

import numpy as np

from app.services.infrastructure.dataset_reader import DatasetMetadata
from app.services.infrastructure.raw_metadata import read_raw_metadata


class DATReader:
    """Read raw C-order data shaped as projections x height x width."""

    def __init__(self, file_path: str):
        self.path = Path(file_path)
        if not self.path.exists():
            raise FileNotFoundError(f"DAT file not found: {file_path}")
    
        metadata = read_raw_metadata(self.path)
        self.width = int(metadata.get("width", 2048))
        self.height = int(metadata.get("height", 2048))
        self.dtype = np.dtype(metadata.get("dtype", "float32"))
        self.dtype_str = str(self.dtype)
        self.bytes_per_element = self.dtype.itemsize
    
        file_size = self.path.stat().st_size
        bytes_per_projection = self.width * self.height * self.bytes_per_element
    
        if bytes_per_projection == 0:
            raise ValueError(f"Invalid dimensions for DAT file: {self.width}x{self.height}")
    
        if file_size % bytes_per_projection != 0:
            raise ValueError(
                f"File size {file_size} B does not match expected DAT dimensions "
                f"{self.width}x{self.height} ({self.dtype})"
            )
    
        inferred_count = file_size // bytes_per_projection
        requested_count = metadata.get("projection_count", inferred_count)
        if int(requested_count) != inferred_count:
            raise ValueError(
                f"DAT sidecar projection_count ({requested_count}) "
                f"does not match calculated file count ({inferred_count})"
            )
    
        self.projection_count = inferred_count
        if self.projection_count == 0:
            raise ValueError(f"DAT file is empty: {self.path}")
    
        # Map directly into 3D shape (projections, height, width)
        self._volume = np.memmap(
            self.path,
            dtype=self.dtype,
            mode="r",
            shape=(self.projection_count, self.height, self.width)
        )

    def get_metadata(self) -> DatasetMetadata:
        return DatasetMetadata(
            filename=self.path.name,
            format="DAT",
            width=self.width,
            height=self.height,
            dtype=str(self.dtype),
            projection_count=self.projection_count,
            detector_height=self.height,
            detector_width=self.width,
        )

    def load_projection(self, frame_index: int) -> np.ndarray:
        self._validate_frame_index(frame_index)
        return np.array(self._volume[frame_index])

    def load_sinogram(self, slice_index: int) -> np.ndarray:
        self._validate_slice_index(slice_index)
        return np.array(self._volume[:, slice_index, :])

    def close(self) -> None:
        """Release the local memory map."""
        if hasattr(self, "_mapped_data"):
            del self._volume
            self._mapped_data._mmap.close()
            del self._mapped_data

    def __del__(self) -> None:
        try:
            self.close()
        except (AttributeError, ValueError):
            pass

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