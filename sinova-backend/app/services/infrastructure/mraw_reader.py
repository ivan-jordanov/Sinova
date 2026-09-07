"""
MRAW file format reader with memory-mapped access.

MRAW is a raw binary format commonly used in CT imaging.
This module provides efficient access to large MRAW files
without loading the entire file into memory.
"""

from pathlib import Path

import numpy as np
import pyMRAW

from app.services.infrastructure.dataset_reader import DatasetMetadata

MRAWMetadata = DatasetMetadata


class MRAWReader:
    """
    Reads MRAW files with memory-mapped access.

    MRAW files are flat binary arrays of detector readings.
    This reader assumes a standard layout: projections × height × width.
    """


    def __init__(self, file_path: str):
        """
        Initialize reader for a Photron MRAW file.

        Args:
            file_path: Path to the .mraw file

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file appears to be invalid MRAW
        """
        self.path = Path(file_path)
        if not self.path.exists():
            raise FileNotFoundError(f"MRAW file not found: {file_path}")

        # pyMRAW returns (images, info)
        images, info = pyMRAW.load_video(str(self.path))

        # Extract dimensions from metadata dict or directly from the mapped array
        if isinstance(info, dict):
            self.width = int(info.get("width", images.shape[2]))
            self.height = int(info.get("height", images.shape[1]))
        else:
            self.height, self.width = images.shape[1], images.shape[2]

        # Photron MRAW files store raw 12-bit data as uint16 (2 bytes per pixel)
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

        # Map raw data directly to 3D array (projections, height, width)
        self._volume = np.memmap(
            self.path,
            dtype=self.dtype,
            mode="r",
            shape=(self.projection_count, self.height, self.width),
        )

    def get_metadata(self) -> MRAWMetadata:
        """Get metadata for this MRAW file."""
        return MRAWMetadata(
            filename=self.path.name,
            format="MRAW",
            width=self.width,
            height=self.height,
            dtype=self.dtype_str,
            projection_count=self.projection_count,
            detector_height=self.height,
            detector_width=self.width,
        )

    def load_projection(self, frame_index: int) -> np.ndarray:
        """
        Load a single projection frame from disk.

        Uses memory mapping to avoid loading the entire file.

        Args:
            frame_index: Which projection to load (0 to projection_count-1)

        Returns:
            2D array of shape (height, width)

        Raises:
            ValueError: If frame_index is out of bounds
        """
        if not (0 <= frame_index < self.projection_count):
            raise ValueError(
                f"Frame index {frame_index} out of bounds "
                f"(0 to {self.projection_count - 1})"
            )

        return np.array(self._volume[frame_index])

    def load_sinogram(self, slice_index: int) -> np.ndarray:
        """
        Load a sinogram (cross-section through all projections).

        A sinogram is a horizontal slice through the CT data,
        showing how a single row changes across all projections.

        Args:
            slice_index: Which horizontal line to extract (0 to height-1)

        Returns:
            2D array of shape (projection_count, width)

        Raises:
            ValueError: If slice_index is out of bounds
        """
        if not (0 <= slice_index < self.height):
            raise ValueError(
                f"Slice index {slice_index} out of bounds (0 to {self.height - 1})"
            )

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
