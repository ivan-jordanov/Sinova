from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.core.config import AVAILABLE_OPERATIONS
from app.schemas.preprocessing import (
    ApplyPreprocessingRequest,
    JobStatus,
    OperationInfo,
)
from app.services.business.dataset_access import get_dataset_service
from app.services.business.job_manager import ProcessingJob, get_job_manager
from app.services.processing.processing_parallel import run_preprocessing_job

router = APIRouter(prefix="/preprocessing", tags=["preprocessing"])



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