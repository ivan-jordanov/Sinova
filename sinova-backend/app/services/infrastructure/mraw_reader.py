from pathlib import Path

import numpy as np
import pyMRAW

from app.services.infrastructure.dataset_reader import DatasetMetadata

MRAWMetadata = DatasetMetadata


class MRAWReader:
    """
    Reads MRAW files with memory-mapped access.

    MRAW files are flat binary arrays of detector readings.
    This reader assumes a standard layout: projections * height * width.
    """

    def __init__(self, file_path: str):
        self.path = Path(file_path)
        if not self.path.exists():
            raise FileNotFoundError(f"MRAW file not found: {file_path}")

        images, info = pyMRAW.load_video(str(self.path))

        if isinstance(info, dict):
            self.width = int(info.get("width", images.shape[2]))
            self.height = int(info.get("height", images.shape[1]))
        else:
            self.height, self.width = images.shape[1], images.shape[2]

        self.dtype = np.uint16
        self.dtype_str = str(self.dtype)
        self.bytes_per_element = self.dtype().itemsize

        file_size = self.path.stat().st_size
        bytes_per_projection = self.width * self.height * self.bytes_per_element

        if file_size % bytes_per_projection != 0:
            raise ValueError(
                f"File size ({file_size} B) does not match expected "
                f"MRAW dimensions {self.width}x{self.height} ({self.dtype.__name__})"
            )

        self.projection_count = file_size // bytes_per_projection
        if self.projection_count == 0:
            raise ValueError(f"MRAW file is empty: {self.path}")

        self._volume = np.memmap(
            self.path,
            dtype=self.dtype,
            mode="r",
            shape=(self.projection_count, self.height, self.width),
        )
        

    def get_metadata(self) -> MRAWMetadata:
        return MRAWMetadata(
            filename=self.path.name,
            format="MRAW",
            width=self.width,
            height=self.height,
            dtype=self.dtype_str,
            detector_height=self.height,
            detector_width=self.width,
            projection_count=self.projection_count
        )

    def load_projection(self, frame_index: int) -> np.ndarray:
        if not (0 <= frame_index < self.projection_count):
            raise ValueError(
                f"Frame index {frame_index} out of bounds "
                f"(0 to {self.projection_count - 1})"
            )

        return np.asarray(self._volume[frame_index]).copy()

    def load_sinogram(self, slice_index: int) -> np.ndarray:
        if not (0 <= slice_index < self.height):
            raise ValueError(
                f"Slice index {slice_index} out of bounds (0 to {self.height - 1})"
            )

        return np.asarray(self._volume[:, slice_index, :]).copy()

    def close(self) -> None:
        if hasattr(self, "_volume") and self._volume is not None:
            try:
                if hasattr(self._volume, "_mmap") and self._volume._mmap:
                    self._volume._mmap.close()
            except (AttributeError, ValueError):
                pass
            del self._volume

    def __del__(self) -> None:
        try:
            self.close()
        except (AttributeError, ValueError):
            pass