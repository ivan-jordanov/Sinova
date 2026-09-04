from uuid import uuid4

from app.schemas.preview import PreviewRequest, PreviewResponse


def create_preview(request: PreviewRequest) -> PreviewResponse:
    return PreviewResponse(
        context=request.context,
        width=2,
        height=2,
        data_format="json-placeholder",
        dtype="float32",
        data=[0.0, 0.0, 0.0, 0.0],
        request_id=str(uuid4()),
        message=(
            "Preview accepted. Real float32 application/octet-stream data "
            "will replace this placeholder."
        ),
    )