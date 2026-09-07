import asyncio
from fastapi import APIRouter, HTTPException

from app.core.config import OPERATION_DEPENDENCIES
from app.schemas.preprocessing import (
    ApplyPreprocessingRequest,
    JobStatus,
    OperationInfo,
)
from app.services.business.job_manager import get_job_manager

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
    OperationInfo(
        id="6",
        name="FOV Mask",
        short_name="fov_mask",
        category="spatial",
        description="Apply field-of-view masking",
        requires=[],
    ),
    OperationInfo(
        id="7",
        name="COR",
        short_name="cor",
        category="geometry",
        description="Apply center-of-rotation correction",
        requires=[],
    ),
    OperationInfo(
        id="8",
        name="Clip Attenuation",
        short_name="clip_attenuation",
        category="intensity",
        description="Clip attenuation values",
        requires=[],
    ),
]


@router.get("/operations", response_model=list[OperationInfo])
def get_operations() -> list[OperationInfo]:
    """
    Get list of available operations and their dependencies.

    Frontend calls this once to display available operations
    and understand which operations require which dependencies.

    Returns:
        List of available operations with their constraints
    """
    return AVAILABLE_OPERATIONS


@router.post("/apply", response_model=JobStatus)
def apply(request: ApplyPreprocessingRequest) -> JobStatus:
    """
    Submit a preprocessing job to apply operations to the entire dataset.

    Validates the configuration, creates a job, starts background processing,
    and returns immediately with the job ID.

    Args:
        request: Preprocessing configuration to apply

    Returns:
        Job status with job_id and initial progress

    Raises:
        HTTPException 422: If configuration is invalid
    """
    try:
        # Validate operation order
        request.configuration.validate_operation_order()
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Create job
    job_manager = get_job_manager()
    job_id = job_manager.create_job(request.configuration)

    # Start background task
    # This is simple for single-server deployments
    # Production would use Celery or similar
    asyncio.create_task(run_preprocessing_job(job_id))

    # Return immediately with job ID
    job = job_manager.get_job(job_id)
    return JobStatus(
        id=job.id,
        status=job.status,
        progress=job.progress,
        message=job.message,
        current_operation=job.current_operation,
        error=job.error,
        created_at=job.created_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )


@router.get("/status/{job_id}", response_model=JobStatus)
def status(job_id: str) -> JobStatus:
    """
    Get the status of a preprocessing job.

    Args:
        job_id: ID of the job to query

    Returns:
        Current job status including progress and message

    Raises:
        HTTPException 404: If job ID not found
    """
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return JobStatus(
        id=job.id,
        status=job.status,
        progress=job.progress,
        message=job.message,
        current_operation=job.current_operation,
        error=job.error,
        created_at=job.created_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )


@router.post("/cancel/{job_id}", response_model=JobStatus)
def cancel(job_id: str) -> JobStatus:
    """
    Cancel a preprocessing job.

    Only works if the job is still queued or running.

    Args:
        job_id: ID of the job to cancel

    Returns:
        Updated job status

    Raises:
        HTTPException 404: If job ID not found
    """
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job = job_manager.cancel_job(job_id)

    return JobStatus(
        id=job.id,
        status=job.status,
        progress=job.progress,
        message=job.message,
        current_operation=job.current_operation,
        error=job.error,
        created_at=job.created_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )


async def run_preprocessing_job(job_id: str) -> None:
    """
    Background task that executes a preprocessing job.

    Loads the active dataset, applies operations to each frame/slice,
    and updates progress. This is a placeholder that tracks progress
    but doesn't yet save results to disk.

    Args:
        job_id: ID of the job to process
    """
    job_manager = get_job_manager()
    job = job_manager.start_job(job_id)

    if not job:
        return

    try:
        from app.services.business.dataset_access import (
            DatasetNotLoaded,
            get_dataset_service,
        )
        from app.services.business.operation_executor import (
            apply_operations_to_data,
        )

        dataset_service = get_dataset_service()

        if not dataset_service.is_loaded():
            raise DatasetNotLoaded("No dataset loaded")

        # Get dataset info
        metadata = dataset_service.get_metadata()
        total_projections = metadata["projection_count"]

        # Process each projection
        for frame_idx in range(total_projections):
            # Allow cancellation
            if job.status == "cancelled":
                return

            # Update progress
            progress = int((frame_idx / total_projections) * 100)
            job_manager.update_progress(
                job_id,
                progress,
                f"Processing frame {frame_idx + 1}/{total_projections}",
                current_operation="apply_operations",
            )

            # Load and process frame
            frame = dataset_service.get_projection(frame_idx)
            processed = apply_operations_to_data(frame, job.configuration)

            # TODO: Save processed frame to job workspace
            # For now, just process and move on

            # Yield to event loop occasionally
            if frame_idx % 10 == 0:
                await asyncio.sleep(0.01)

        # Mark job as complete
        job_manager.complete_job(job_id, "All frames processed successfully")

    except Exception as e:
        job_manager.fail_job(job_id, str(e))