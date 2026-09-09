from fastapi import APIRouter, HTTPException
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

from app.schemas.dataset import (
    BrowseResponse,
    DatasetMetadata,
    LoadDatasetRequest,
    LoadDatasetResponse,
)
from app.services.business.dataset_access import get_dataset_service
from app.services.infrastructure.io_service import validate_path

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/browse", response_model=BrowseResponse)
def browse_file() -> BrowseResponse:
    """
    Triggers a native OS file picker dialog on the host server machine
    and returns the selected full file path.
    """
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the main Tkinter window
        root.attributes("-topmost", True)  # Bring file dialog to the front

        selected_path = filedialog.askopenfilename(
            title="Select Dataset File",
            filetypes=[
                ("Dataset Files", "*.dat *.dicom *.tif *.tiff *.mraw"),
                ("All Files", "*.*"),
            ],
        )
        root.destroy()

        if not selected_path:
            raise HTTPException(status_code=400, detail="No file selected")

        # Convert backslashes to standard forward slashes or resolved path string
        clean_path = str(Path(selected_path).resolve())

        return BrowseResponse(path=clean_path)

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500, detail=f"Failed to open OS file picker: {str(e)}"
        )


@router.post("/load", response_model=LoadDatasetResponse)
def load(request: LoadDatasetRequest) -> LoadDatasetResponse:
    try:
        # 1. Run validation and keep the returned resolved Path
        validated_path = validate_path(request.path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        # 2. Pass the validated Path (or string) to dataset_service
        dataset_service = get_dataset_service()
        metadata = dataset_service.load_dataset(str(validated_path))

        return LoadDatasetResponse(
            loaded=True,
            metadata=DatasetMetadata(
                name=metadata["filename"],
                detector_width=metadata["detector_width"],
                detector_height=metadata["detector_height"],
                projections=metadata["projection_count"],
                format=metadata["format"],
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load dataset: {str(e)}",
        )


@router.post("/unload")
def unload() -> dict[str, bool]:
    """Unloads the active dataset and releases memory and file handles."""
    try:
        dataset_service = get_dataset_service()
        dataset_service.unload_dataset()
        return {"unloaded": True}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to unload dataset: {str(e)}",
        )


@router.get("/metadata", response_model=DatasetMetadata)
def metadata() -> DatasetMetadata:
    """
    Get metadata for the currently loaded dataset.
    """
    try:
        dataset_service = get_dataset_service()
        if not dataset_service.is_loaded():
            raise HTTPException(
                status_code=400,
                detail="No dataset loaded. Call /ingestion/load first.",
            )

        meta = dataset_service.get_metadata()
        return DatasetMetadata(
            name=meta["filename"],
            detector_width=meta["detector_width"],
            detector_height=meta["detector_height"],
            projections=meta["projection_count"],
            slices=meta["detector_height"],
            format=meta["format"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get metadata: {str(e)}",
        )