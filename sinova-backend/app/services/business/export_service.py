"""Export service for saving processed data to disk."""
from pathlib import Path
from typing import Literal

import numpy as np


class ExportService:
    """Handles exporting processed CT data to various formats."""

    def __init__(self, output_dir: str = "./data/exports"):
        """
        Initialize export service.

        Args:
            output_dir: Directory where exported files will be saved
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_npy(self, data: np.ndarray, filename: str) -> str:
        """
        Export data as NumPy .npy file.

        Args:
            data: Array to export
            filename: Output filename (without .npy extension)

        Returns:
            Path to exported file

        Raises:
            OSError: If file cannot be written
        """
        output_path = self.output_dir / f"{filename}.npy"
        np.save(output_path, data)
        return str(output_path)

    def export_tiff(self, data: np.ndarray, filename: str) -> str:
        """
        Export data as TIFF image.

        Args:
            data: 2D array to export (assumes 8-bit or 16-bit)
            filename: Output filename (without .tiff extension)

        Returns:
            Path to exported file

        Raises:
            ImportError: If PIL is not available
            OSError: If file cannot be written
        """
        from PIL import Image

        output_path = self.output_dir / f"{filename}.tiff"

        # Convert to appropriate uint format
        if data.dtype == np.float32 or data.dtype == np.float64:
            # Scale from 0-1 to 0-65535 for 16-bit
            if data.max() <= 1.0:
                data_uint16 = (data * 65535).astype(np.uint16)
            else:
                data_uint16 = np.clip(data, 0, 65535).astype(np.uint16)
            img = Image.fromarray(data_uint16, mode="I;16")
        else:
            img = Image.fromarray(data)

        img.save(output_path)
        return str(output_path)

    def export_mraw(self, data: np.ndarray, filename: str) -> str:
        """
        Export 3D data as MRAW binary file.

        Args:
            data: 3D array of shape (projections, height, width)
            filename: Output filename (without .mraw extension)

        Returns:
            Path to exported file

        Raises:
            ValueError: If data is not 3D
            OSError: If file cannot be written
        """
        if data.ndim != 3:
            raise ValueError(f"Expected 3D array, got {data.ndim}D")

        output_path = self.output_dir / f"{filename}.mraw"

        # Flatten and save as binary float32
        data_flat = data.astype(np.float32).flatten()
        data_flat.tofile(output_path)

        return str(output_path)

    def verify_export(self, filepath: str) -> bool:
        """
        Verify that exported file exists and is readable.

        Args:
            filepath: Path to the exported file

        Returns:
            True if file exists and is readable
        """
        path = Path(filepath)
        return path.exists() and path.stat().st_size > 0
