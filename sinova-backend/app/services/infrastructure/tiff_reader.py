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
    
            # Open initial file using tifffile memory mapping
            initial_memmap = tifffile.memmap(self.path, mode="r")
    
            # 3D multi-page TIFF file (single file containing all slices)
            if initial_memmap.ndim == 3:
                self._volume = initial_memmap
                self.projection_count, self.height, self.width = self._volume.shape
                self.dtype = self._volume.dtype
            # 2D TIFF slice: check if part of a multi-file series in the directory
            elif initial_memmap.ndim == 2:
                search_dir = self.path.parent if self.path.is_file() else self.path
                tiff_series = sorted([
                    f for f in search_dir.iterdir()
                    if f.is_file() and f.suffix.lower() in (".tif", ".tiff")
                ])
    
                # Standalone single-slice TIFF file
                if len(tiff_series) <= 1:
                    self._volume = initial_memmap
                    self.projection_count = 1
                    self.height, self.width = self._volume.shape
                    self.dtype = self._volume.dtype
                # Series of single-slice TIFF files
                else:
                    first_frame = tifffile.imread(str(tiff_series[0]))
                    self.projection_count = len(tiff_series)
                    self.height, self.width = first_frame.shape[-2], first_frame.shape[-1]
                    self.dtype = first_frame.dtype
    
                    cache_file = search_dir / "_tiff_memmap.dat"
                    print(f"Creating temporary file-backed memmap: {cache_file}")
    
                    self._volume = np.memmap(
                        cache_file,
                        dtype=self.dtype,
                        mode="w+",
                        shape=(self.projection_count, self.height, self.width)
                    )
    
                    for i, filepath in enumerate(tiff_series):
                        self._volume[i, :, :] = tifffile.imread(str(filepath))
    
                    self._volume.flush()
            else:
                raise ValueError(f"Unsupported TIFF dimensions: {initial_memmap.ndim}D")

            self.dtype_str = str(self.dtype)
            self.bytes_per_element = np.dtype(self.dtype).itemsize
    
    def close(self) -> None:
        """Release memmap file resources and remove temporary disk cache."""
        if getattr(self, "_volume", None) is not None:
            if hasattr(self._volume, "flush"):
                self._volume.flush()

            mmap_obj = getattr(self._volume, "_mmap", None)
            if mmap_obj is not None:
                mmap_obj.close()

            del self._volume
            self._volume = None

        search_dir = self.path.parent if self.path.is_file() else self.path
        cache_file = search_dir / "_tiff_memmap.dat"
        if cache_file.exists():
            cache_file.unlink()

        # Delete disk cache file created during initial series load
        search_dir = self.path.parent if self.path.is_file() else self.path
        cache_file = search_dir / "_tiff_memmap.dat"
        if cache_file.exists():
            try:
                cache_file.unlink()
            except OSError:
                pass

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
        
        # Slice from volume directly
        if self._volume.ndim == 3:
            return np.asarray(self._volume[frame_index, :, :]).copy()
        
        # Single 2D frame fallback
        return np.asarray(self._volume).copy()

    def load_sinogram(self, slice_index: int) -> np.ndarray:
        self._validate_slice_index(slice_index)
        
        # Vectorized 3D slicing across all projection frames
        if self._volume.ndim == 3:
            return np.asarray(self._volume[:, slice_index, :]).copy()
        
        # Single 2D frame fallback
        return np.asarray(self._volume[slice_index, :]).copy()

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