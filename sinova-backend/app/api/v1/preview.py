from fastapi import APIRouter

from app.schemas.preview import PreviewRequest, PreviewResponse
from app.services.preview_service import create_preview

router = APIRouter(prefix="/preview", tags=["preview"])


@router.post("/projection", response_model=PreviewResponse)
def projection(request: PreviewRequest) -> PreviewResponse:
    return create_preview(request)


@router.post("/sinogram", response_model=PreviewResponse)
def sinogram(request: PreviewRequest) -> PreviewResponse:
    return create_preview(request)
