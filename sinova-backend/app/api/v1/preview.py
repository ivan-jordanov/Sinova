from uuid import uuid4

from fastapi import APIRouter, HTTPException
import numpy as np

from app.schemas.preview import PreviewRequest, PreviewResponse
from app.services.business.dataset_access import (
    DatasetNotLoaded,
    get_dataset_service,
)
from app.services.business.operation_executor import apply_operations_to_data

router = APIRouter(prefix="/preview", tags=["preview"])


@router.post("/projection", response_model=PreviewResponse)
def projection(request: PreviewRequest) -> PreviewResponse:
    try:
        dataset_service = get_dataset_service()

        if not dataset_service.is_loaded():
            raise HTTPException(
                status_code=400,
                detail="No dataset loaded. Call /ingestion/load first.",
            )

        frame_data = dataset_service.get_projection(request.slice)

        if request.mode == "original":
            processed = frame_data
        else:
            try:
                request.configuration.validate_operation_order()
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))

            processed = apply_operations_to_data(frame_data, request.configuration)

        processed = np.ascontiguousarray(processed, dtype=np.float32)

        data_min = float(np.min(processed)) if processed.size > 0 else 0.0
        data_max = float(np.max(processed)) if processed.size > 0 else 1.0

        return PreviewResponse(
            context="projection",
            width=int(processed.shape[1]),
            height=int(processed.shape[0]),
            data_format="json-float32",
            dtype="float32",
            data=processed.flatten().tolist(),
            min_value=data_min,
            max_value=data_max,
            request_id=str(uuid4()),
            message=f"Projection preview computed ({request.mode or 'current'})",
        )

    except DatasetNotLoaded as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (ValueError, EOFError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid frame request: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate projection preview: {str(e)}",
        )


@router.post("/sinogram", response_model=PreviewResponse)
def sinogram(request: PreviewRequest) -> PreviewResponse:
    try:
        dataset_service = get_dataset_service()

        if not dataset_service.is_loaded():
            raise HTTPException(
                status_code=400,
                detail="No dataset loaded. Call /ingestion/load first.",
            )

        sinogram_data = dataset_service.get_sinogram(request.slice)

        if request.mode == "original":
            processed = sinogram_data
        else:
            try:
                request.configuration.validate_operation_order()
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e))

            processed = apply_operations_to_data(sinogram_data, request.configuration)

        processed = np.ascontiguousarray(processed, dtype=np.float32)

        data_min = float(np.min(processed)) if processed.size > 0 else 0.0
        data_max = float(np.max(processed)) if processed.size > 0 else 1.0

        return PreviewResponse(
            context="sinogram",
            width=int(processed.shape[1]),
            height=int(processed.shape[0]),
            data_format="json-float32",
            dtype="float32",
            data=processed.flatten().tolist(),
            min_value=data_min,
            max_value=data_max,
            request_id=str(uuid4()),
            message=f"Sinogram preview computed ({request.mode or 'current'})",
        )

    except DatasetNotLoaded as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (ValueError, EOFError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid slice request: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate sinogram preview: {str(e)}",
        )