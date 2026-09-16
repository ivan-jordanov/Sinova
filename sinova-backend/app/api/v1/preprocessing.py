from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.core.config import OPERATION_SCOPES
from app.schemas.preprocessing import (
    ApplyPreprocessingRequest,
    JobStatus,
    OperationInfo,
)
from app.services.business.dataset_access import get_dataset_service
from app.services.business.job_manager import ProcessingJob, get_job_manager
from app.services.business.operation_executor import run_preprocessing_job

router = APIRouter(prefix="/preprocessing", tags=["preprocessing"])

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


def _job_to_response(job: ProcessingJob) -> JobStatus:
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


@router.get("/operations", response_model=list[OperationInfo])
def get_operations() -> list[OperationInfo]:
    return AVAILABLE_OPERATIONS


@router.post("/apply", response_model=JobStatus)
def apply(
    request: ApplyPreprocessingRequest,
    background_tasks: BackgroundTasks,
) -> JobStatus:
    try:
        request.configuration.validate_operation_order()
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    dataset_service = get_dataset_service()
    if not dataset_service.is_loaded():
        raise HTTPException(status_code=400, detail="No dataset loaded. Call /ingestion/load first.")

    job_manager = get_job_manager()
    job_id = job_manager.create_job(request.configuration)

    background_tasks.add_task(run_preprocessing_job, job_id)

    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=500, detail="Failed to initialize job")

    return _job_to_response(job)


@router.get("/status/{job_id}", response_model=JobStatus)
def status(job_id: str) -> JobStatus:
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return _job_to_response(job)


@router.post("/cancel/{job_id}", response_model=JobStatus)
def cancel(job_id: str) -> JobStatus:
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job = job_manager.cancel_job(job_id)
    return _job_to_response(job)