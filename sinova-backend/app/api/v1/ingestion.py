from fastapi import APIRouter, HTTPException

from app.schemas.dataset import (
    DatasetMetadata,
    LoadDatasetRequest,
    LoadDatasetResponse,
)
from app.services.business.dataset_access import get_dataset_service
from app.services.infrastructure.io_service import validate_path

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/load", response_model=LoadDatasetResponse)
def load(request: LoadDatasetRequest) -> LoadDatasetResponse:
    """
    Load a dataset file and return its metadata.

    Validates the file path, then reads metadata without loading
    the entire file into memory.

    Args:
        request: Contains file_path to load

    Returns:
        Metadata about the loaded dataset

    Raises:
        HTTPException 400: If path is invalid or file format unsupported
    """
    try:
        # Validate path (security + existence checks)
        validate_path(request.path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        # Load dataset and get metadata
        dataset_service = get_dataset_service()
        metadata = dataset_service.load_dataset(request.path)

        # Convert metadata to response format (snake_case to camelCase)
        return LoadDatasetResponse(
            loaded=True,
            metadata=DatasetMetadata(
                name=metadata["filename"],
                detector_width=metadata["detector_width"],
                detector_height=metadata["detector_height"],
                projections=metadata["projection_count"],
                slices=metadata["detector_height"],  # For sinogram slices
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


@router.get("/metadata", response_model=DatasetMetadata)
def metadata() -> DatasetMetadata:
    """
    Get metadata for the currently loaded dataset.

    Returns:
        Metadata about the active dataset

    Raises:
        HTTPException 400: If no dataset is currently loaded
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