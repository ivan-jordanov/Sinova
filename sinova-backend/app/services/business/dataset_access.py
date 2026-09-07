"""
Dataset access service.

Provides a unified interface for loading dataset metadata and data.
Format-specific details stay inside infrastructure readers.
"""
import numpy as np

from app.services.infrastructure.dat_reader import DATReader
from app.services.infrastructure.dataset_reader import DatasetMetadata, DatasetReader
from app.services.infrastructure.dicom_reader import DICOMReader
from app.services.infrastructure.io_service import validate_path
from app.services.infrastructure.mraw_reader import MRAWReader
from app.services.infrastructure.tiff_reader import TIFFReader


class DatasetNotLoaded(Exception):
    """Raised when trying to access a dataset that hasn't been loaded."""

    pass


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

    def load_dataset(self, file_path: str) -> DatasetMetadata:
        """
        Load a dataset from disk.

        Args:
            file_path: Path to the dataset file

        Returns:
            Dataset metadata

        Raises:
            ValueError: If path is invalid or file format is not supported
            FileNotFoundError: If file does not exist
        """
        # Validate path (security check, size check, existence check)
        validated_path = validate_path(file_path)

        # Determine format from extension
        suffix = validated_path.suffix.lower()

        reader_type = self._reader_type(validated_path)
        self._close_reader()
        self.reader = reader_type(str(validated_path))
        self.metadata = self.reader.get_metadata()
        self.current_path = str(validated_path)

        return self.metadata

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
        if self.reader is not None:
            close = getattr(self.reader, "close", None)
            if close is not None:
                close()

    @staticmethod
    def _reader_type(path):
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
        try:
            return readers[path.suffix.lower()]
        except KeyError as error:
            supported = ", ".join(sorted(readers))
            raise ValueError(
                f"Unsupported format: {path.suffix or path.name}. "
                f"Supported formats: {supported} and DICOM directories"
            ) from error


# Global dataset service instance
_dataset_service = DatasetService()


def get_dataset_service() -> DatasetService:
    """Get the global dataset service instance."""
    return _dataset_service
