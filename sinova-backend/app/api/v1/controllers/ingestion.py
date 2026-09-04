from fastapi import APIRouter

from app.schemas.dataset import (
    DatasetMetadata,
    LoadDatasetRequest,
    LoadDatasetResponse,
)
from app.services.dataset_service import get_metadata, load_dataset

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/load", response_model=LoadDatasetResponse)
def load(request: LoadDatasetRequest) -> LoadDatasetResponse:
    return LoadDatasetResponse(loaded=True, metadata=load_dataset(request.path))


@router.get("/metadata", response_model=DatasetMetadata)
def metadata() -> DatasetMetadata:
    return get_metadata()