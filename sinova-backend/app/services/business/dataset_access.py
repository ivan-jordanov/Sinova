"""
Dataset access service.

Provides a unified interface for loading dataset metadata and data.
Format-specific details stay inside infrastructure readers.
"""
from pathlib import Path
import numpy as np

from app.services.infrastructure.dat_reader import DATReader
from app.services.infrastructure.dataset_reader import DatasetMetadata, DatasetReader
from app.services.infrastructure.dicom_reader import DICOMReader
from app.services.infrastructure.io_service import validate_path
from app.services.infrastructure.mraw_reader import MRAWReader
from app.services.infrastructure.tiff_reader import TIFFReader


class DatasetNotLoaded(Exception):
    """Raised when an operation attempts to access a dataset that has not been loaded."""

    def __init__(self, message: str = "No dataset is currently loaded.") -> None:
        self.message = message
        super().__init__(self.message)


class DatasetService:
    """
    Provides access to loaded datasets.

    This service manages the current active dataset and provides
    efficient access to projections and sinograms.
    """

    def __init__(self):
        """Initialize the dataset service."""
        self.current_path: str | None = None
        self.reader: DatasetReader | None = None
        self.metadata: DatasetMetadata | None = None
        self.rot_center: float | None = None
        self.crop_y: tuple[int, int] | None = None
        self.flat_reader: DatasetReader | None = None
        self.flat_metadata: DatasetMetadata | None = None
        self.dark_reader: DatasetReader | None = None
        self.dark_metadata: DatasetMetadata | None = None

    def load_dataset(self, file_path: str) -> DatasetMetadata:
        """
        Load a dataset from disk.

        Args:
            file_path: Path to the dataset file or directory

        Returns:
            Dataset metadata

        Raises:
            ValueError: If path is invalid or file format is not supported
            FileNotFoundError: If file does not exist
        """
        validated_path = validate_path(file_path)
        reader_type = self._reader_type(validated_path)

        self._close_reader()

        try:
            reader = reader_type(str(validated_path))
            metadata = reader.get_metadata()
        except Exception:
            self._close_reader()
            raise

        self.reader = reader
        self.metadata = metadata
        self.current_path = str(validated_path)

        return self.metadata
    
    def load_normalization(
    self,
    flat_path: str | None = None,
    dark_path: str | None = None,
    ) -> tuple[DatasetMetadata | None, DatasetMetadata | None]:
        """
        Load flat and/or dark reference datasets for normalization.
    
        Args:
            flat_path: Optional path to the flat field file
            dark_path: Optional path to the dark field file
    
        Returns:
            Tuple containing (metadata_flat, metadata_dark)
        """
        metadata_flat: DatasetMetadata | None = None
        metadata_dark: DatasetMetadata | None = None
    
        if flat_path:
            validated_flat = validate_path(flat_path)
            flat_reader_type = self._reader_type(validated_flat)
            self.flat_reader = flat_reader_type(str(validated_flat))
            metadata_flat = self.flat_reader.get_metadata()
            self.flat_metadata = metadata_flat
    
        if dark_path:
            validated_dark = validate_path(dark_path)
            dark_reader_type = self._reader_type(validated_dark)
            self.dark_reader = dark_reader_type(str(validated_dark))
            metadata_dark = self.dark_reader.get_metadata()
            self.dark_metadata = metadata_dark
    
        return metadata_flat, metadata_dark

    def get_metadata(self) -> DatasetMetadata:
        """
        Get metadata for the currently loaded dataset.

        Returns:
            Dataset metadata

        Raises:
            DatasetNotLoaded: If no dataset is currently loaded
        """
        if self.metadata is None:
            raise DatasetNotLoaded("No dataset loaded")

        return self.metadata

    def get_projection(self, frame_index: int) -> np.ndarray:
        """
        Load a single projection frame.

        Args:
            frame_index: Which projection to load

        Returns:
            2D array of shape (height, width)

        Raises:
            DatasetNotLoaded: If no dataset is loaded
            ValueError: If frame index is out of bounds
        """
        if self.reader is None:
            raise DatasetNotLoaded("No dataset loaded")

        return self.reader.load_projection(frame_index)

    def get_sinogram(self, slice_index: int) -> np.ndarray:
        """
        Load a sinogram (horizontal slice through all projections).

        Args:
            slice_index: Which horizontal slice to load

        Returns:
            2D array of shape (projection_count, width)

        Raises:
            DatasetNotLoaded: If no dataset is loaded
            ValueError: If slice index is out of bounds
        """
        if self.reader is None:
            raise DatasetNotLoaded("No dataset loaded")

        return self.reader.load_sinogram(slice_index)

    def is_loaded(self) -> bool:
        """Check if a dataset is currently loaded."""
        return self.reader is not None and self.metadata is not None

    def _close_reader(self) -> None:
        """Safely close active reader resources for main, flat, and dark datasets."""
        for attr in ("reader", "flat_reader", "dark_reader"):
            reader_obj = getattr(self, attr, None)
            if reader_obj is not None:
                if hasattr(reader_obj, "close"):
                    reader_obj.close()
                setattr(self, attr, None)

    def unload_dataset(self) -> None:
        """Unload active dataset and normalization references, release file handles, and reset state."""
        self._close_reader()
        self.metadata = None
        self.flat_metadata = None
        self.dark_metadata = None
        self.current_path = None
        self.rot_center = None
        self.crop_y = None
        
    def update_geometry_bounds(
        self,
        rot_center: float | None = None,
        crop_y: tuple[int, int] | None = None,
    ) -> None:
        """Update geometric rotation center and vertical cropping bounds."""
        if rot_center is not None:
            self.rot_center = rot_center

        if crop_y is not None:
            self.crop_y = crop_y

    @staticmethod
    def _reader_type(path: Path) -> type[DatasetReader]:
        """Resolve reader type from file path or directory structure."""
        if path.is_dir():
            return DICOMReader

        readers = {
            ".mraw": MRAWReader,
            ".dat": DATReader,
            ".tif": TIFFReader,
            ".tiff": TIFFReader,
            ".dcm": DICOMReader,
            ".dicom": DICOMReader,
        }

        suffix = path.suffix.lower()
        if suffix in readers:
            return readers[suffix]

        supported = ", ".join(sorted(readers.keys()))
        raise ValueError(
            f"Unsupported format: {suffix or path.name}. "
            f"Supported formats: {supported} and DICOM directories"
        )


# Global dataset service instance
_dataset_service = DatasetService()


def get_dataset_service() -> DatasetService:
    """Get the global dataset service instance."""
    return _dataset_service