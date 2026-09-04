from fastapi import APIRouter

from app.schemas.preprocessing import (
    ApplyPreprocessingRequest,
    ProcessingStatus,
)

router = APIRouter(prefix="/preprocessing", tags=["preprocessing"])


@router.post("/apply", response_model=ProcessingStatus)
def apply(request: ApplyPreprocessingRequest) -> ProcessingStatus:
    operation_count = len(request.configuration.operations)
    return ProcessingStatus(
        status="queued",
        job_id="mock-processing-job",
        message=f"Accepted {operation_count} configured operations.",
    )


@router.get("/status", response_model=ProcessingStatus)
def status() -> ProcessingStatus:
    return ProcessingStatus(status="idle", message="No processing job is running.")