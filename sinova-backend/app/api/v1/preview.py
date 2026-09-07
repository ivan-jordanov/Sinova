from uuid import uuid4

from fastapi import APIRouter, HTTPException

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
    and returns the processed data.

    Args:
        request: Contains slice index and preprocessing configuration

    Returns:
        Processed projection data as float32 array

    Raises:
        HTTPException 400: If no dataset loaded or invalid slice index
    """
    try:
        dataset_service = get_dataset_service()

        if not dataset_service.is_loaded():
            raise HTTPException(
                status_code=400,
                detail="No dataset loaded. Call /ingestion/load first.",
            )

        # Load the projection frame
        frame_data = dataset_service.get_projection(request.slice)

        # Apply preprocessing operations
        processed = apply_operations_to_data(frame_data, request.configuration)

        # Convert to flat list for JSON serialization
        # TODO: In production, send as binary octet-stream
        data_list = processed.flatten().tolist()

        return PreviewResponse(
            context="projection",
            width=processed.shape[1],
            height=processed.shape[0],
            data_format="json-float32",
            dtype="float32",
            data=data_list,
            request_id=str(uuid4()),
            message="Projection preview computed",
        )

    except DatasetNotLoaded as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        # Could be invalid slice index or operation error
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate preview: {str(e)}",
        )


@router.post("/sinogram", response_model=PreviewResponse)
def sinogram(request: PreviewRequest) -> PreviewResponse:
    """
    Generate a preview of a sinogram (horizontal slice) with preprocessing applied.

    Loads the sinogram, applies all enabled operations,
    and returns the processed data.

    Args:
        request: Contains slice index and preprocessing configuration

    Returns:
        Processed sinogram data as float32 array

    Raises:
        HTTPException 400: If no dataset loaded or invalid slice index
    """
    try:
        dataset_service = get_dataset_service()

        if not dataset_service.is_loaded():
            raise HTTPException(
                status_code=400,
                detail="No dataset loaded. Call /ingestion/load first.",
            )

        # Load the sinogram (horizontal cross-section)
        sinogram_data = dataset_service.get_sinogram(request.slice)

        # Apply preprocessing operations
        processed = apply_operations_to_data(sinogram_data, request.configuration)

        # Convert to flat list for JSON serialization
        # TODO: In production, send as binary octet-stream
        data_list = processed.flatten().tolist()

        return PreviewResponse(
            context="sinogram",
            width=processed.shape[1],
            height=processed.shape[0],
            data_format="json-float32",
            dtype="float32",
            data=data_list,
            request_id=str(uuid4()),
            message="Sinogram preview computed",
        )

    except DatasetNotLoaded as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        # Could be invalid slice index or operation error
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate sinogram preview: {str(e)}",
        )
