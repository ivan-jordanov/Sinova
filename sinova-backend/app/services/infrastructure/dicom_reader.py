"""DICOM image and DICOM series reader."""
from pathlib import Path
import numpy as np
import pydicom
from pydicom.errors import InvalidDicomError

from app.services.infrastructure.dataset_reader import DatasetMetadata


class DICOMReader:
    """Read a multi-frame DICOM file or a directory containing a DICOM series."""

    def __init__(self, file_path: str):
        self.path = Path(file_path)
        if not self.path.exists():
            raise FileNotFoundError(f"DICOM path not found: {file_path}")

        self._pydicom = pydicom
        self.files = self._find_files()

        # Read header of the first file to inspect metadata
        first_dcm = self._pydicom.dcmread(str(self.files[0]))
        first_frame = first_dcm.pixel_array

        # Single multi-frame DICOM file
        if len(self.files) == 1 and first_frame.ndim == 3:
            self._volume = first_frame
            self.projection_count, self.height, self.width = self._volume.shape
            self.dtype = self._volume.dtype
        # Series of single-frame DICOM files
        else:
            self.projection_count = len(self.files)
            self.height, self.width = first_frame.shape[-2], first_frame.shape[-1]
            self.dtype = first_frame.dtype

            # Create temporary file-backed memmap buffer
            cache_dir = self.path if self.path.is_dir() else self.path.parent
            cache_file = cache_dir / "_dicom_memmap.dat"

            print(f"Creating temporary file-backed memmap: {cache_file}")
            self._volume = np.memmap(
                cache_file,
                dtype=self.dtype,
                mode="w+",
                shape=(self.projection_count, self.height, self.width),
            )

            for i, filepath in enumerate(self.files):
                dcm = self._pydicom.dcmread(str(filepath))
                self._volume[i, :, :] = dcm.pixel_array

            self._volume.flush()

        self.dtype_str = str(self.dtype)
        self.bytes_per_element = np.dtype(self.dtype).itemsize

    def get_metadata(self) -> DatasetMetadata:
        return DatasetMetadata(
            filename=self.path.name,
            format="DICOM",
            width=self.width,
            height=self.height,
            dtype=self.dtype_str,
            projection_count=self.projection_count,
            detector_height=self.height,
            detector_width=self.width,
        )

    def load_projection(self, frame_index: int) -> np.ndarray:
        self._validate_frame_index(frame_index)
        return np.asarray(self._volume[frame_index]).copy()

    def load_sinogram(self, slice_index: int) -> np.ndarray:
        self._validate_slice_index(slice_index)
        return np.asarray(self._volume[:, slice_index, :]).copy()

    def _find_files(self) -> list[Path]:
        search_dir = self.path.parent if self.path.is_file() else self.path

        valid_files = []
        for candidate in search_dir.iterdir():
            if not candidate.is_file() or candidate.name.startswith("_"):
                continue

            try:
                self._pydicom.dcmread(str(candidate), stop_before_pixels=True)
                valid_files.append(candidate)
            except InvalidDicomError:
                continue

        if not valid_files:
            raise FileNotFoundError(f"No valid DICOM files found in {search_dir}")

        # Sort files by actual DICOM InstanceNumber to guarantee correct slice ordering
        valid_files.sort(key=self._instance_number)
        return valid_files

    def _instance_number(self, path: Path) -> int:
        try:
            dataset = self._pydicom.dcmread(str(path), stop_before_pixels=True)
            return int(getattr(dataset, "InstanceNumber", 0))
        except Exception:
            return 0

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