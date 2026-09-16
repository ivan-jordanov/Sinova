import json
from pathlib import Path
from typing import Any, Literal
import numpy as np
import tifffile
import pydicom
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid


class ExportService:
    """Handles streaming export of processed CT data to disk."""

    def __init__(self, output_dir: str = "./data/exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _check_cancellation(self, job_manager: Any | None, job_id: str | None) -> bool:
        if job_manager and job_id:
            job = job_manager.get_job(job_id)
            return job is not None and job.status == "cancelled"
        return False

    def _report_progress(
        self,
        job_manager: Any | None,
        job_id: str | None,
        frame_idx: int,
        total_frames: int,
        message: str,
    ) -> None:
        if job_manager and job_id:
            if frame_idx % 10 == 0 or frame_idx == total_frames - 1:
                progress = 80 + int(((frame_idx + 1) / total_frames) * 20)
                job_manager.update_progress(
                    job_id,
                    progress,
                    message,
                    current_operation="export_pass",
                )

    def export_tiff_stream(
        self,
        workspace_volume: np.memmap,
        filename: str,
        job_id: str | None = None,
        job_manager: Any | None = None,
    ) -> str:
        """Stream 3D volume frame-by-frame to a multi-page TIFF file."""
        output_path = self.output_dir / f"{filename}.tiff"
        num_frames = workspace_volume.shape[0]

        with tifffile.TiffWriter(output_path, bigtiff=True) as tw:
            for i in range(num_frames):
                if self._check_cancellation(job_manager, job_id):
                    return ""

                frame = np.asarray(workspace_volume[i, :, :], dtype=np.float32)
                tw.write(frame, contiguous=True)
                self._report_progress(
                    job_manager,
                    job_id,
                    i,
                    num_frames,
                    f"Exporting TIFF: frame {i + 1}/{num_frames}",
                )

        return str(output_path)

    def export_mraw_stream(
        self,
        workspace_volume: np.memmap,
        filename: str,
        job_id: str | None = None,
        job_manager: Any | None = None,
    ) -> str:
        """Stream 3D volume frame-by-frame to a raw float32 binary MRAW file."""
        output_path = self.output_dir / f"{filename}.mraw"
        num_frames = workspace_volume.shape[0]

        with open(output_path, "wb") as f:
            for i in range(num_frames):
                if self._check_cancellation(job_manager, job_id):
                    return ""

                frame_bytes = workspace_volume[i, :, :].astype(np.float32, copy=False).tobytes()
                f.write(frame_bytes)
                self._report_progress(
                    job_manager,
                    job_id,
                    i,
                    num_frames,
                    f"Exporting MRAW: frame {i + 1}/{num_frames}",
                )

        return str(output_path)

    def export_dat_stream(
        self,
        workspace_volume: np.memmap,
        filename: str,
        job_id: str | None = None,
        job_manager: Any | None = None,
    ) -> str:
        """Stream 3D volume to a raw binary .dat file and matching JSON sidecar."""
        dat_path = self.output_dir / f"{filename}.dat"
        json_path = self.output_dir / f"{filename}.json"
        num_frames, height, width = workspace_volume.shape

        with open(dat_path, "wb") as f:
            for i in range(num_frames):
                if self._check_cancellation(job_manager, job_id):
                    return ""

                frame_bytes = workspace_volume[i, :, :].astype(np.float32, copy=False).tobytes()
                f.write(frame_bytes)
                self._report_progress(
                    job_manager,
                    job_id,
                    i,
                    num_frames,
                    f"Exporting DAT: frame {i + 1}/{num_frames}",
                )

        metadata = {
            "width": width,
            "height": height,
            "projection_count": num_frames,
            "dtype": "float32",
            "offset": 0,
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return str(dat_path)

    def export_dicom_series(
        self,
        workspace_volume: np.memmap,
        folder_name: str,
        job_id: str | None = None,
        job_manager: Any | None = None,
    ) -> str:
        """Stream 3D volume slice-by-slice to a folder of 2D DICOM files."""

        series_dir = self.output_dir / folder_name
        series_dir.mkdir(parents=True, exist_ok=True)

        num_frames, height, width = workspace_volume.shape
        study_uid = generate_uid()
        series_uid = generate_uid()

        for i in range(num_frames):
            if self._check_cancellation(job_manager, job_id):
                return ""

            file_meta = FileMetaDataset()
            file_meta.MediaStorageHostName = "CT_PREPROCESS"
            file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.2"
            file_meta.MediaStorageSOPInstanceUID = generate_uid()
            file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

            dcm_path = series_dir / f"slice_{i:04d}.dcm"
            ds = FileDataset(str(dcm_path), {}, file_meta=file_meta, preamble=b"\0" * 128)
            ds.PatientName = "Anonymous"
            ds.PatientID = "CT_DATASET"
            ds.Modality = "CT"
            ds.StudyInstanceUID = study_uid
            ds.SeriesInstanceUID = series_uid
            ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
            ds.SOPClassUID = file_meta.MediaStorageSOPClassUID

            ds.Rows = height
            ds.Columns = width
            ds.BitsAllocated = 32
            ds.BitsStored = 32
            ds.HighBit = 31
            ds.PixelRepresentation = 1
            ds.SamplesPerPixel = 1
            ds.PhotometricInterpretation = "MONOCHROME2"
            ds.InstanceNumber = i + 1

            frame = np.asarray(workspace_volume[i, :, :], dtype=np.float32)
            ds.PixelData = frame.tobytes()
            ds.save_as(str(dcm_path))

            self._report_progress(
                job_manager,
                job_id,
                i,
                num_frames,
                f"Exporting DICOM: slice {i + 1}/{num_frames}",
            )

        return str(series_dir)
    
    def verify_export(self, filepath: str) -> bool:
        """
        Verify that exported file or directory exists and contains data.
        Supports single files (.tiff, .mraw, .dat) and directories (DICOM series).
        """
        if not filepath:
            return False

        path = Path(filepath)
        if not path.exists():
            return False

        if path.is_file():
            return path.stat().st_size > 0

        if path.is_dir():
            return any(f.is_file() and f.stat().st_size > 0 for f in path.iterdir())

        return False

    def export_data(
        self,
        workspace_volume: np.memmap,
        filename: str,
        export_format: Literal["tiff", "mraw", "dat", "dicom"] = "tiff",
        job_id: str | None = None,
        job_manager: Any | None = None,
    ) -> str:
        """Dispatch export request to target format handler."""
        fmt = export_format.lower()
        if fmt == "tiff" or fmt == "tif":
            return self.export_tiff_stream(
                workspace_volume, filename, job_id=job_id, job_manager=job_manager
            )
        elif fmt == "mraw":
            return self.export_mraw_stream(
                workspace_volume, filename, job_id=job_id, job_manager=job_manager
            )
        elif fmt == "dat":
            return self.export_dat_stream(
                workspace_volume, filename, job_id=job_id, job_manager=job_manager
            )
        elif fmt == "dicom" or fmt == "dcm":
            return self.export_dicom_series(
                workspace_volume, filename, job_id=job_id, job_manager=job_manager
            )
        else:
            raise ValueError(f"Unsupported export format: {export_format}")