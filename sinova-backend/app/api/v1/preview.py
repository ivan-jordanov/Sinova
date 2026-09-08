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
    """
    Generate a preview of a projection frame with preprocessing applied.

    Loads the specified projection, applies all enabled operations,
    and returns the processed data with intensity range metadata.
    """
    try:
        dataset_service = get_dataset_service()

        if not dataset_service.is_loaded():
            raise HTTPException(
                status_code=400,
                detail="No dataset loaded. Call /ingestion/load first.",
            )

        # Load projection frame and apply preprocessing
        frame_data = dataset_service.get_projection(request.slice)
        #processed = apply_operations_to_data(frame_data, request.configuration)
        processed = frame_data  # Skip for now, as preprocessing is not yet implemented

        # Ensure contiguous float32 buffer
        processed = np.ascontiguousarray(processed, dtype=np.float32)

        # Compute min/max stats for frontend canvas intensity scaling
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
            message="Projection preview computed",
        )

    except DatasetNotLoaded as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (ValueError, EOFError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid frame request: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate projection preview: {str(e)}",
        )


@router.post("/sinogram", response_model=PreviewResponse)
def sinogram(request: PreviewRequest) -> PreviewResponse:
    """
    Generate a preview of a sinogram (horizontal slice) with preprocessing applied.

    Loads the sinogram, applies all enabled operations,
    and returns the processed data with intensity range metadata.
    """
    try:
        dataset_service = get_dataset_service()

        if not dataset_service.is_loaded():
            raise HTTPException(
                status_code=400,
                detail="No dataset loaded. Call /ingestion/load first.",
            )

        # Load sinogram and apply preprocessing operations
        sinogram_data = dataset_service.get_sinogram(request.slice)
        #processed = apply_operations_to_data(sinogram_data, request.configuration)
        processed = sinogram_data  # Skip for now, as preprocessing is not yet implemented

        # Ensure contiguous float32 buffer
        processed = np.ascontiguousarray(processed, dtype=np.float32)

        # Compute min/max stats for frontend canvas intensity scaling
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
            message="Sinogram preview computed",
        )

    except DatasetNotLoaded as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (ValueError, EOFError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid slice request: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate sinogram preview: {str(e)}",
        )