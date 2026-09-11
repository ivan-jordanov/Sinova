"""MRAW dataset reader using the pyMRAW library."""
from pathlib import Path
import numpy as np
import pyMRAW

from app.services.infrastructure.dataset_reader import DatasetMetadata


class MRAWReader:
    """Reads MRAW files using pyMRAW memory-mapped access."""

    def __init__(self, file_path: str):
        self.path = Path(file_path)
        if not self.path.exists():
            raise FileNotFoundError(f"MRAW file not found: {file_path}")

        cih_path = self.path.with_suffix(".cih")
        cihx_path = self.path.with_suffix(".cihx")

        if cih_path.exists():
            header_path = cih_path
        elif cihx_path.exists():
            header_path = cihx_path
        else:
            raise FileNotFoundError(
                f"No corresponding .cih or .cihx header file found for: {file_path}"
            )

        try:
            images, _ = pyMRAW.load_video(str(header_path))
        except ValueError as err:
            if "Unknown format code" in str(err):
                images = self._load_memmap_fallback(header_path)
            else:
                raise

        self._volume = images
        self.projection_count = images.shape[0]
        self.height = images.shape[1]
        self.width = images.shape[2]

        self.dtype = images.dtype
        self.dtype_str = str(self.dtype)
        self.bytes_per_element = np.dtype(self.dtype).itemsize

    def _load_memmap_fallback(self, header_path: Path) -> np.memmap:
        """Fallback when pyMRAW crashes on string fields in CIH headers."""
        width = None
        height = None

        with open(header_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if ":" in line or "=" in line:
                    delim = ":" if ":" in line else "="
                    parts = line.split(delim, 1)
                    key = parts[0].strip().lower()
                    val = parts[1].strip()

                    if key in ("image width", "width"):
                        width = int(val)
                    elif key in ("image height", "height"):
                        height = int(val)

        if not width or not height:
            raise ValueError(
                f"Could not parse width/height from CIH header: {header_path}"
            )

        file_size = self.path.stat().st_size
        bytes_per_frame = width * height * 2
        projection_count = file_size // bytes_per_frame

        return np.memmap(
            self.path,
            dtype=np.uint16,
            mode="r",
            shape=(projection_count, height, width),
        )

    def close(self) -> None:
        """Release memmap file resources."""
        if getattr(self, "_volume", None) is not None:
            mmap_obj = getattr(self._volume, "_mmap", None)
            if mmap_obj is not None:
                mmap_obj.close()
            del self._volume
            self._volume = None

    def __del__(self) -> None:
        self.close()

    def get_metadata(self) -> DatasetMetadata:
        return DatasetMetadata(
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
        self._validate_frame_index(frame_index)
        return np.asarray(self._volume[frame_index, :, :]).copy()

    def load_sinogram(self, slice_index: int) -> np.ndarray:
        self._validate_slice_index(slice_index)
        return np.asarray(self._volume[:, slice_index, :]).copy()

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
            
    def get_data(self) -> np.ndarray:
        """Return the full dataset array as a NumPy array."""
        return np.asarray(self._volume)