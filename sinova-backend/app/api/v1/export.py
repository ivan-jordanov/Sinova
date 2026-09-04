from fastapi import APIRouter

from app.schemas.export import ExportRequest, ExportResponse

router = APIRouter(prefix="/export", tags=["export"])


@router.post("", response_model=ExportResponse)
def export(request: ExportRequest) -> ExportResponse:
    return ExportResponse(
        accepted=True,
        job_id="mock-export-job",
        message=f"Export to {request.format} accepted as a placeholder.",
    )