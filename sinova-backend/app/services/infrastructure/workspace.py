# app/services/infrastructure/workspace.py
import tempfile
from pathlib import Path
import numpy as np

class ProcessingWorkspace:
    """File-backed workspace for multi-pass dataset processing."""
    
    def __init__(self, job_id: str, shape: tuple[int, int, int]):
        self.job_id = job_id
        self.shape = shape
        self.file_path = Path(tempfile.gettempdir()) / f"workspace_{job_id}.dat"
        
        self._volume = np.memmap(
            self.file_path,
            dtype=np.float32,
            mode="w+",
            shape=self.shape
        )

    def write_projection(self, index: int, data: np.ndarray) -> None:
        self._volume[index, :, :] = data

    def read_sinogram(self, index: int) -> np.ndarray:
        return np.asarray(self._volume[:, index, :]).copy()

    def write_sinogram(self, index: int, data: np.ndarray) -> None:
        self._volume[:, index, :] = data

    def flush(self) -> None:
        if hasattr(self._volume, "flush"):
            try:
                self._volume.flush()
            except OSError:
                pass

    def close(self) -> None:
        self.flush()
        
        mmap_obj = getattr(self._volume, "_mmap", None)
        if mmap_obj is not None:
            try:
                mmap_obj.close()
            except (OSError, ValueError):
                pass

        del self._volume
        self._volume = None

        if self.file_path.exists():
            try:
                self.file_path.unlink()
            except OSError:
                pass

    def __del__(self) -> None:
        self.close()