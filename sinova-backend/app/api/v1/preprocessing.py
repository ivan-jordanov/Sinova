from fastapi import APIRouter, HTTPException

from app.core.config import OPERATION_DEPENDENCIES
from app.schemas.preprocessing import (
    ApplyPreprocessingRequest,
    OperationInfo,
    ProcessingStatus,
)

router = APIRouter(prefix="/preprocessing", tags=["preprocessing"])

# Define available operations with metadata (for frontend constraint display)
AVAILABLE_OPERATIONS = [
    OperationInfo(
        id="1",
        name="Normalize",
        short_name="normalize",
        category="intensity",
        description="Normalize intensity values",
        requires=[],
    ),
    OperationInfo(
        id="2",
        name="Negative Log",
        short_name="negative_log",
        category="intensity",
        description="Apply negative log transformation",
        requires=["normalize"],
    ),
    OperationInfo(
        id="3",
        name="Denoise",
        short_name="denoise",
        category="spatial",
        description="Reduce noise in image",
        requires=[],
    ),
    OperationInfo(
        id="4",
        name="Ring Filter",
        short_name="ring_filter",
        category="spatial",
        description="Remove ring artifacts",
        requires=[],
    ),
    OperationInfo(
        id="5",
        name="Edge Enhance",
        short_name="edge_enhance",
        category="spatial",
        description="Enhance edges",
        requires=["denoise"],
    ),
]


@router.get("/operations", response_model=list[OperationInfo])
def get_operations() -> list[OperationInfo]:
    """Get available operations and their dependencies for frontend constraint display."""
    return AVAILABLE_OPERATIONS


@router.post("/apply", response_model=ProcessingStatus)
def apply(request: ApplyPreprocessingRequest) -> ProcessingStatus:
    """Accept preprocessing configuration and queue a job."""
    try:
        # Validate operation order
        request.configuration.validate_operation_order()
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    operation_count = len(request.configuration.operations)
    return ProcessingStatus(
        status="queued",
        job_id="mock-processing-job",
        message=f"Accepted {operation_count} configured operations.",
    )


@router.get("/status", response_model=ProcessingStatus)
def status() -> ProcessingStatus:
    return ProcessingStatus(status="idle", message="No processing job is running.")