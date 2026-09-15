import asyncio
from fastapi import APIRouter, HTTPException

from app.core.config import OPERATION_DEPENDENCIES, OPERATION_SCOPES
from app.schemas.preprocessing import (
    ApplyPreprocessingRequest,
    JobStatus,
    OperationInfo,
    ResolveOperationRequest,
    ResolveOperationResponse,
)
from app.services.business.dataset_access import DatasetNotLoaded, get_dataset_service
from app.services.business.operation_executor import resolve_broad_scope_operation
from app.services.business.job_manager import get_job_manager

router = APIRouter(prefix="/preprocessing", tags=["preprocessing"])

# Define available operations with metadata (for frontend constraint display)
AVAILABLE_OPERATIONS = [
    OperationInfo(
        id="normalization",
        name="Normalization",
        short_name="normalize",
        category="intensity",
        description="Normalize intensity values using flat/dark references",
        requires=[],
        scope=OPERATION_SCOPES["normalize"],
    ),
    OperationInfo(
        id="attenuation",
        name="Attenuation Clipping",
        short_name="clip_attenuation",
        category="intensity",
        description="Clip attenuation values to a specified threshold",
        requires=[],
        scope=OPERATION_SCOPES["clip_attenuation"],
    ),
    OperationInfo(
        id="fov-mask",
        name="FOV / Beam Mask",
        short_name="fov_mask",
        category="spatial",
        description="Define circular spatial mask across detector coordinates",
        requires=[],
        scope=OPERATION_SCOPES["fov_mask"],
    ),
    OperationInfo(
        id="crop-pad-beam",
        name="Crop & Pad Beam",
        short_name="crop_pad_beam",
        category="spatial",
        description="Crop and pad detector beam boundary regions",
        requires=[],
        scope=OPERATION_SCOPES["crop_pad_beam"],
    ),
    OperationInfo(
        id="denoise",
        name="Denoise Filter",
        short_name="denoise",
        category="spatial",
        description="Apply median or Gaussian spatial filtering",
        requires=[],
        scope=OPERATION_SCOPES["denoise"],
    ),
    OperationInfo(
        id="cor_shift",
        name="Center of Rotation",
        short_name="cor_shift",
        category="geometry",
        description="Set the detector center used by geometry-aware operations",
        requires=[],
        scope=OPERATION_SCOPES["cor_shift"],
    ),
    OperationInfo(
        id="fourier-wavelet",
        name="Fourier-Wavelet",
        short_name="ring_filter_fw",
        category="destriping",
        description="Remove ring artifacts using frequency and wavelet decomposition",
        requires=[],
        scope=OPERATION_SCOPES["ring_filter_fw"],
    ),
    OperationInfo(
        id="vo-sorting",
        name="Vo's Sorting",
        short_name="ring_filter_vo",
        category="destriping",
        description="Remove ring artifacts using Nghia Vo's sorting method",
        requires=[],
        scope=OPERATION_SCOPES["ring_filter_vo"],
    ),
    OperationInfo(
        id="neural",
        name="Neural Destriping",
        short_name="neural",
        category="destriping",
        description="Remove ring artifacts using deep neural model processing",
        requires=[],
        scope=OPERATION_SCOPES["neural"],
    ),
]

@router.get("/operations", response_model=list[OperationInfo])
def get_operations() -> list[OperationInfo]:
    return AVAILABLE_OPERATIONS


@router.post("/resolve", response_model=ResolveOperationResponse)
def resolve_operation(request: ResolveOperationRequest) -> ResolveOperationResponse:
    """
    Resolve an operation's broad-scope parameters (e.g. COR estimation) into
    concrete values. Call this once when the user enables/needs an
    auto-estimated parameter; store the result back into the frontend's
    configuration. Preview and /apply then see plain values, same as any
    manually-entered parameter.
    """

    dataset_service = get_dataset_service()

    try:
        if not dataset_service.is_loaded():
            raise HTTPException(status_code=400, detail="No dataset loaded.")

        resolved_parameters = resolve_broad_scope_operation(
            request.short_name, request.parameters, dataset_service, request.context,
        )
    except DatasetNotLoaded as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ResolveOperationResponse(parameters=resolved_parameters)


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