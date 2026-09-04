from fastapi import APIRouter, HTTPException

from app.schemas.dataset import (
    DatasetMetadata,
    LoadDatasetRequest,
    LoadDatasetResponse,
)
from app.services.dataset_service import get_metadata, load_dataset
from app.services.io_service import validate_path

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/load", response_model=LoadDatasetResponse)
def load(request: LoadDatasetRequest) -> LoadDatasetResponse:
    try:
        # Validate that the path is safe and accessible
        validate_path(request.path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return LoadDatasetResponse(loaded=True, metadata=load_dataset(request.path))


@router.get("/metadata", response_model=DatasetMetadata)
def metadata() -> DatasetMetadata:
    return get_metadata()